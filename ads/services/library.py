
""" Interact with the ADS library service. """

import json
import re
from collections import ChainMap, namedtuple
from peewee import (Database, SqliteDatabase, Select, Insert, Update, Delete, ForeignKeyAccessor, ForeignKeyField)

from ads.client import Client
from ads.utils import flatten

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
        self.database = database or Client()

    def execute(self, query, **kwargs):
        if isinstance(query, Select):

            # If there is an expression given that requires a specific ID, then we should retrieve that
            # because it may be a public library that is not owned by the user.
            kwds = []
            with self.database as client:
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
                            #params=dict(rows=20_000_000)
                        )
                        kwds.append(response.json["metadata"])
                        #kwds[-1]["documents"] = response.json["documents"]

            # Now bind the model to an in-memory database so that we evaluate the query.
            model = query.model
            local_database = SqliteDatabase(":memory:")
            with local_database.bind_ctx([model], bind_refs=False, bind_backrefs=False):
                local_database.create_tables([model])

                for _kwds in kwds:
                    model.create(**_kwds)

                local_query = model.select()\
                                   .where(query._where)\
                                   .order_by(query._order_by)\
                                   .limit(query._limit)

                return local_query.execute().cursor

        elif isinstance(query, Insert):
            
            field_names = {"name", "description", "public", "bibcode"}
            data = { k.name: v for k, v in query._insert.items() if k.name in field_names }

            # TODO: Warn about ignored fields.
            with self.database as client:
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
                
                # Update metadata.
                metadata_field_names = {"name", "description", "public"}
                dirty_metadata_field_names = set(data).intersection(metadata_field_names)
                if dirty_metadata_field_names:
                    update_metadata = { k: data[k] for k in dirty_metadata_field_names }
                    with self.database as client:
                        client.api_request(
                            f"biblib/documents/{library_id}",
                            data=json.dumps(update_metadata),
                            method="put"
                        )
                
                # Update permissions.
                '''
                if "permissions" in data:
                    _, all_permission_kinds = valid_permissions([])
                    for email in data["permissions"]:
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

                        with self.database as client:
                            client.api_request(
                                f"biblib/permissions/{library_id}",
                                data=json.dumps(update_permissions),
                                method="post"
                            )

                        print(f"Update permissions for  {update_permissions}")
                '''

                # Update documents.
                if data.get("documents", None) is not None:
                    # Of the form {'add': {'2018A&A...616A...1G'}, 'remove': set()}
                    with self.database as client:
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
                    
                    with self.database as client:
                        client.api_request(
                            f"biblib/documents/{library_id}",
                            data=json.dumps(dict(email=owner)),
                            method="post"
                        )

                return Cursor(library_id)
                
            
            elif isinstance(query, Delete):
                with self.database as client:
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
    
    payload = dict(action=action)
    if libraries:
        payload["libraries"] = [library.id for library in libraries]

    with Client() as client:
        response = client.api_request(
            f"biblib/libraries/operations/{library.id}",
            data=json.dumps(payload),
            method="post",
        )

    if return_new_library:
        new = library.__class__(**response.json)
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


class DocumentsAccessor(ForeignKeyAccessor):

    def get_rel_instance(self, instance):
        try:
            return instance._documents
        except AttributeError:
            bibcodes = instance.__data__.get("documents", None)
            if bibcodes is None:
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
            return instance._documents

    def __set__(self, instance, obj):
        if obj is None:
            super().__set__(instance, obj)
        else:
            instance._documents = obj
            instance._dirty.add("documents")

class DocumentArrayField(ForeignKeyField):
    accessor_class = DocumentsAccessor

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

