
""" Interact with the ADS library service. """

import json
import re
from collections import ChainMap, namedtuple
from peewee import (Database, SqliteDatabase, Select, Insert, Update, Delete, ForeignKeyAccessor, ForeignKeyField)

from ads.client import Client
from ads.utils import flatten, to_bibcode

Cursor = namedtuple("Cursor", ["lastrowid", "rowcount"], defaults=[1])

def valid_email_address(email: str) -> bool:
    """
    Check whether an email address looks valid.
    
    :param email:
        An email address.
    """
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def valid_permissions(values):
    permissions = ("read", "write", "admin")
    unknown = set(values).difference(permissions)
    is_valid = (len(unknown) == 0)
    return (is_valid, permissions)


from peewee import Node, Expression


### These kinds of recursive searches/matches will be refactored at some point.

def request_library_ids(expression):
    if expression is None:
        return [None]
    calls = []
    sides = (expression.lhs, expression.rhs)
    for side, other_side in (sides, sides[::-1]):
        if isinstance(side, Expression):
            calls.extend(request_library_ids(side))
        elif isinstance(side, Node):
            if side.model.__name__ == "Library" and side.name == "id":
                calls.append(other_side)
            else:
                # Should make sure we are requesting all libraries back.
                calls.append(None)
            
    return list(set(calls))


class LibraryInterface(Database):

    def init(self, database=None, *args):
        self.database = database 
        
    def execute(self, query, **kwargs):
        if isinstance(query, Select):

            # If there is an expression given that requires a specific ID, then we should retrieve that
            # because it may be a public library that is not owned by the user.
            kwds = []
            bibcodes = {}
            with Client() as client:
                for library_id in request_library_ids(query._where):
                    if library_id is None:
                        # Retrieve all listing.
                        response = client.api_request(f"biblib/libraries")
                        kwds.extend(response.json["libraries"])
                    else:
                        # If we requested a specific library then we get the documents here.
                        # TODO: Need some clever magic to avoid extra API call to retrieve documents AGAIN.
                        response = client.api_request(
                            f"biblib/libraries/{library_id}",
                            # If we don't specify a number of rows, we only get 20.
                            # Let's request the maximum that we think could exist.
                            params=dict(rows=20_000_000)
                        )
                        bibcodes[response.json["metadata"]["id"]] = response.json["documents"]
                        kwds.append(response.json["metadata"])
                        #kwds[-1]["documents"] = response.json["documents"]

            # Now bind the model to an in-memory database so that we evaluate the query.
            model = query.model
            local_database = SqliteDatabase(":memory:")
            from ads.services.search import MockCursor

            with local_database.bind_ctx([model], bind_refs=False, bind_backrefs=False):
                local_database.create_tables([model])

                for _kwds in kwds:
                    model.create(**_kwds)

                local_query = model.select()\
                                   .where(query._where)\
                                   .order_by(query._order_by)\
                                   .limit(query._limit)

                foo = local_query.execute().cursor
                results = []
                field_names = [field.name for field in local_query._returning]
                for field_values in foo:

                    kwds = dict(zip(field_names, field_values))
                    if kwds["id"] in bibcodes:
                        kwds["documents"] = bibcodes[kwds["id"]]
                    results.append(kwds)

                return MockCursor(local_query, results)

        elif isinstance(query, Insert):
            data = {}
            print("Insert", query._insert)
            for k, v in query._insert.items():
                if k.name in ("name", "description", "public"):
                    data[k.name] = v
                elif k.name == "documents":
                    if isinstance(v, dict):
                        raise a
                        data["bibcode"] = v["add"]
                    else:
                        data["bibcode"] = list(map(to_bibcode, v))

            #print(f"Inserting {data}")
            # TODO: Warn about ignored fields.
            with Client() as client:
                response = client.api_request(
                    f"biblib/libraries",
                    method="post",
                    data=json.dumps(data)
                )
            # A hack to return the ID without specifying `_returning`:
            # we put the ID in the `rowcount` attribute
            return Cursor(response.json["id"], response.json["id"])


        elif isinstance(query, (Update, Delete)):
            # TODO: Check that the where expression is by ID only, or its forbidden.
            library_id = query._where.rhs
            assert query._where.lhs.name == "id" and query._where.op == "="

            if isinstance(query, Update):
                data = { k.name: v for k, v in query._update.items() }
                
                print(f"Updating {data}")
                # TODO: Should this check go somewhere else? Because when we get
                #       to this point the user has to get a fresh copy of the library
                #       or reset thne value to its original, and update ._dirty
                read_only_field_names = {"id", "num_users", "num_documents", "date_created", "date_last_modified"}
                ignore_fields = set(data).intersection(read_only_field_names)
                if ignore_fields:
                    raise ValueError(f"Cannot update fields {', '.join(ignore_fields)}: these cannot be edited directly.")


                # Update metadata.
                metadata_field_names = {"name", "description", "public"}
                dirty_metadata_field_names = set(data).intersection(metadata_field_names)
                if dirty_metadata_field_names:
                    update_metadata = { k: data[k] for k in dirty_metadata_field_names }
                    with Client() as client:
                        r = client.api_request(
                            f"biblib/documents/{library_id}",
                            data=json.dumps(update_metadata),
                            method="put"
                        )
                        print(r, r.json)
                
                # Update permissions.
                if data.get("permissions", None) is not None:
                    _, all_permission_kinds = valid_permissions([])
                    for email in data["permissions"]:
                        if "owner" in data["permissions"][email]:
                            continue
                        print(f"Updating permission for {email}")
                        update_permissions = dict(
                            email=email, 
                            permission={ kind: False for kind in all_permission_kinds}
                        )
                        permission_kinds = data["permissions"].get(email, [])
                        if permission_kinds:
                            update_permissions["permission"].update(
                                dict(zip(permission_kinds, [True] * len(permission_kinds)))
                            )

                        with Client() as client:
                            client.api_request(
                                f"biblib/permissions/{library_id}",
                                data=json.dumps(update_permissions),
                                method="post"
                            )

                        print(f"Update permissions for  {update_permissions}")

                # Update documents.
                if data.get("documents", None) is not None:
                    # Of the form {'add': {'2018A&A...616A...1G'}, 'remove': set()}
                    #print(f'Updating documents for library {library_id} {data["documents"]}')
                    with Client() as client:
                        for action, bibcode in data["documents"].items():
                            if not bibcode: continue
                            response = client.api_request(
                                f"biblib/documents/{library_id}",
                                data=json.dumps(dict(action=action, bibcode=bibcode)),
                                method="post"
                            )
                    

                # Update owner.
                if "owner" in data:
                    owner = data["owner"]
                    if not valid_email_address(owner):
                        raise ValueError(f"Invalid email address for new owner: '{owner}'")
                    
                    with Client() as client:
                        client.api_request(
                            f"biblib/transfer/{library_id}",
                            data=json.dumps(dict(email=owner)),
                            method="post"
                        )

                return Cursor(library_id)
                
            
            elif isinstance(query, Delete):
                with Client() as client:
                    # I assumed that this endpoint would be biblib/libraries/{id},
                    # but it is actually biblib/documents/{id}. I don't know why.
                    # The documentation correctly says biblib/documents/{id}, but
                    # the naming convention is not what I expected.
                    # TODO: Email ADS team about this.
                    #f"biblib/libraries/{self.id}",                    
                    client.api_request(f"biblib/documents/{library_id}", method="delete")
                return Cursor(library_id)



def operation(library, action, libraries=None, return_new_library=False):
    """
    Perform a set operation on one or more libraries.

    :param library:
        The primary library to perform the operation on.

    :param action:
        The name of the action to perform. Must be one of:
            - union
            - intersection
            - difference
            - empty
            - copy
    :param libraries:
        The libraries to perform the action with. This is
        not applicable for the empty action.

    :return:
        Returns the `APIResponse` object.
    """
    action = action.strip().lower()
    available_actions = ("union", "intersection", "difference", "empty", "copy")
    if action not in available_actions:
        raise ValueError(f"Invalid operation action '{action}'. Must be one of {', '.join(available_actions)}")

    if library.id is None or (libraries and (None in [library.id for library in libraries])):
        raise ValueError(f"libraries must be created remotely on ADS before set operations can occur")

    payload = dict(action=action)
    if libraries:
        payload["libraries"] = [library.id for library in libraries]

    from ads import Document
    with Client() as client:
        response = client.api_request(
            f"biblib/libraries/operations/{library.id}",
            data=json.dumps(payload),
            method="post",
        )
        # This sends back the documents as `bibcode` keyword.
        kwds = response.json
        bibcodes = kwds.pop("bibcode")
        if not bibcodes:
            kwds["documents"] = []
        else:
            kwds["documents"] = list(
                Document.select()\
                        .where(Document.bibcode.in_(bibcodes))\
                        .limit(len(bibcodes))
            )

    if return_new_library:
        new = library.__class__(**kwds)
        new._dirty.clear()
        return new
    return None


class Permissions(dict):
    
    def __init__(self, library):
        self._library = library
        self._dirty = set()
        return None

    def __setitem__(self, item, value):
        value = list(set(flatten(value)))
        if not valid_email_address(item):
            raise ValueError(f"Invalid email address '{item}'")
        is_valid, valid_values = valid_permissions(value)
        if not is_valid:
            raise ValueError(f"Invalid permissions among '{value}': must contain only {valid_values}")
        self._set_dirty(item)
        super().__setitem__(item, value)


    def _set_dirty(self, item):
        self._dirty.add(item)
        self._library._dirty.add("permissions")


    def __delitem__(self, item):
        self._set_dirty(item)
        super().__delitem__(item)


    def refresh(self):
        with Client() as client:
            response = client.api_request(f"biblib/permissions/{self._library.id}")
        self.update(dict(ChainMap(*response.json)))
        return response


class NewDocumentsAccessor(ForeignKeyAccessor):


    def get_rel_instance(self, instance):
        print(f"getting {instance}")
        if instance.id is None:
            instance.__data__["documents"] = []
        else:
            # We need to make sure we have a listing from the server.
            if "bibcodes" not in instance.__data__:
                print(f"retrieving")
                with Client() as client:
                    response = client.api_request(
                        f"biblib/libraries/{instance.id}", 
                        params=dict(rows=instance.num_documents)
                    )
                    # TODO: The terminology here in the response is not quite right (eg bibcodes / documents)
                    # Email the ADS team about this.
            
                    # Update any missing metadata.
                    for key, value in response.json["metadata"].items():
                        if instance.__data__.get(key, None) is None:
                            instance.__data__[key] = value
                    #instance._dirty -= set(metadata)

                    instance.__data__["bibcodes"] = response.json["documents"]
                    if instance.__data__.get("num_documents", None) is None:
                        instance.__data__["num_documents"] = len(instance.__data__["bibcodes"])

            # We may have already retrieved them.
            if instance.__data__.get("documents", None) is None:
                from ads import Document
                bibcodes = instance.__data__["bibcodes"]
                if bibcodes:
                    instance.__data__["documents"] = list(
                        Document.select()
                                .where(Document.bibcode.in_(bibcodes))
                                .limit(len(bibcodes))
                    )
                else:
                    instance.__data__["documents"] = []
        return instance.__data__["documents"]

    
    def __set__(self, instance, obj):
        from ads import Document
        print(f"setting {instance} {obj}")
        # Check if the object was created with a list of bibcodes given to the constructor.
        # (The user might have done this, but it's usually how a library is created when we select by specific ID.)
        obj = flatten([obj])
        
        if isinstance(obj, list):
            if all(isinstance(item, str) for item in obj):
                # TODO: we should only believe this if the lbirary is new.
                instance.__data__["bibcodes"] = obj
                if instance.__data__.get("num_documents", None) is None:
                    instance.__data__["num_documents"] = len(obj)

                return None

            elif all(isinstance(item, Document) for item in obj):
                instance.__data__["documents"] = obj
                if instance.__data__.get("num_documents", None) is None:
                    instance.__data__["num_documents"] = len(obj)
            else:
                raise a

        else:
            raise a

            raise a
            obj = flatten([obj])
            instance._dirty.add("documents")

            bibcodes = list(map(to_bibcode, obj))
            instance.__data__["bibcodes"] = bibcodes

            if all(isinstance(doc, Document) for doc in obj):
                instance.__data__["documents"] = obj
            return None
        #return super().__set__(instance, obj)
        

'''
class DocumentsAccessor(ForeignKeyAccessor):

    def get_rel_instance(self, instance):
        try:
            return instance._documents
        except AttributeError:
            bibcodes = instance.__data__.get("documents", None)
            if bibcodes is None:
                if instance.id is None:
                    # Library hasn't been saved yet.
                    bibcodes = instance.__data__["documents"] = []     
                    instance._documents = []               
                else:
                    with Client() as client:
                        response = client.api_request(
                            f"biblib/libraries/{instance.id}", 
                            params=dict(rows=instance.num_documents)
                        )
                        # TODO: The terminology here in the response is not quite right (eg bibcodes / documents)
                        # Email the ADS team about this.
                
                        # Update the metadata.
                        metadata = response.json["metadata"]
                        instance.__data__.update(metadata)
                        instance._dirty -= set(metadata)

                        bibcodes = instance.__data__["documents"] = response.json["documents"]
                    
                    from ads import Document
                    instance._documents = list(
                        Document.select()
                                .where(Document.bibcode.in_(bibcodes))
                                .limit(len(bibcodes))
                    )
            elif len(bibcodes) == 0:
                instance._documents = []
                
            return instance._documents

    def __set__(self, instance, obj):
        if obj is None:
            super().__set__(instance, obj)
        else:
            #print(f"setting documents on {instance} as {obj}")
            instance._documents = flatten(obj)
            instance._dirty.add("documents")
            instance.__data__["num_documents"] = len(instance._documents)

'''
class DocumentArrayField(ForeignKeyField):
    accessor_class = NewDocumentsAccessor

    # We could be creating Document objects here from just the bibcode, but this causes a lot of lazy loading operations.
    # Instead we will let upstream deal with these as bibcodes and make one request.
    python_value = lambda self, value: value


class PermissionsAccessor(ForeignKeyAccessor):

    def get_rel_instance(self, instance):
        try:
            return instance._permissions
        except AttributeError:
            permissions = instance.__data__.get("permissions", None)
            if permissions is None:
                with Client() as client:
                    response = client.api_request(f"biblib/permissions/{instance.id}")
                permissions = dict(ChainMap(*response.json))
                instance.__data__["permissions"] = permissions
            instance._permissions = permissions.copy()

        return instance._permissions
    
    def __set__(self, instance, obj):
        if obj is None:
            super().__set__(instance, obj)
        else:
            instance._permissions = obj
            instance._dirty.add("permissions")

class PermissionsField(ForeignKeyField):
    accessor_class = PermissionsAccessor

