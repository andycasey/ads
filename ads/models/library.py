"""
Library data model.
"""

from inspect import Attribute
from datetime import datetime
from collections import ChainMap
import json
import re
from peewee import (ModelDelete, ModelSelect, Expression, Model, BooleanField, TextField, IntegerField, DateTimeField)
from ads.models.base import ADSAPI
from ads.models.document import Document
from ads.models.hybrid import hybrid_property
from ads.client import Client
from ads.utils import (flatten, to_bibcode)

from peewee import ModelBase, Node, with_metaclass, DoesNotExist, Value, _BoundModelsContext

class SubModel(with_metaclass(ModelBase, Node)):
    def __init__(self, *args, **kwargs):
        if kwargs.pop('__no_default__', None):
            self.__data__ = {}
        else:
            self.__data__ = self._meta.get_default_dict()
        self._dirty = set(self.__data__)
        self.__rel__ = {}

        for k in kwargs:
            setattr(self, k, kwargs[k])

    @classmethod
    def validate_model(cls):
        pass

    @classmethod
    def get(cls, *query, **filters):
        sq = cls.select()
        if query:
            # Handle simple lookup using just the primary key.
            if len(query) == 1 and isinstance(query[0], int):
                sq = sq.where(cls._meta.primary_key == query[0])
            else:
                sq = sq.where(*query)
        if filters:
            sq = sq.filter(**filters)
        return sq.get()

    @classmethod
    def get_or_none(cls, *query, **filters):
        try:
            return cls.get(*query, **filters)
        except DoesNotExist:
            pass

    @classmethod
    def filter(cls, *dq_nodes, **filters):
        return cls.select().filter(*dq_nodes, **filters)

    def get_id(self):
        # Using getattr(self, pk-name) could accidentally trigger a query if
        # the primary-key is a foreign-key. So we use the safe_name attribute,
        # which defaults to the field-name, but will be the object_id_name for
        # foreign-key fields.
        if self._meta.primary_key is not False:
            return getattr(self, self._meta.primary_key.safe_name)

    _pk = property(get_id)

    @_pk.setter
    def _pk(self, value):
        setattr(self, self._meta.primary_key.name, value)

    def _pk_expr(self):
        return self._meta.primary_key == self._pk

    def __hash__(self):
        return hash((self.__class__, self._pk))

    def __eq__(self, other):
        return (
            other.__class__ == self.__class__ and
            self._pk is not None and
            self._pk == other._pk)

    def __ne__(self, other):
        return not self == other

    def __sql__(self, ctx):
        # NOTE: when comparing a foreign-key field whose related-field is not a
        # primary-key, then doing an equality test for the foreign-key with a
        # model instance will return the wrong value; since we would return
        # the primary key for a given model instance.
        #
        # This checks to see if we have a converter in the scope, and that we
        # are converting a foreign-key expression. If so, we hand the model
        # instance to the converter rather than blindly grabbing the primary-
        # key. In the event the provided converter fails to handle the model
        # instance, then we will return the primary-key.
        if ctx.state.converter is not None and ctx.state.is_fk_expr:
            try:
                return ctx.sql(Value(self, converter=ctx.state.converter))
            except (TypeError, ValueError):
                pass

        return ctx.sql(Value(getattr(self, self._meta.primary_key.name),
                             converter=self._meta.primary_key.db_value))

    @classmethod
    def bind(cls, database, bind_refs=True, bind_backrefs=True, _exclude=None):
        is_different = cls._meta.database is not database
        cls._meta.set_database(database)
        if bind_refs or bind_backrefs:
            if _exclude is None:
                _exclude = set()
            G = cls._meta.model_graph(refs=bind_refs, backrefs=bind_backrefs)
            for _, model, is_backref in G:
                if model not in _exclude:
                    model._meta.set_database(database)
                    _exclude.add(model)
        return is_different

    @classmethod
    def bind_ctx(cls, database, bind_refs=True, bind_backrefs=True):
        return _BoundModelsContext((cls,), database, bind_refs, bind_backrefs)



def requires_bibcodes(func):
    def inner(library, *args, **kwargs):
        try:
            library.__data__["bibcodes"]
        except KeyError:
            library.refresh()
        finally:
            return func(library, *args, **kwargs)
    return inner

"""
class LibraryModelBase(ModelBase):
    def __new__(cls, name, bases, attrs):
        new_cls = super(LibraryModelBase, cls).__new__(cls, name, bases, attrs)
        # For the fields, change the accessor.
        #if attrs:
        #    raise a
        print(name, bases, attrs)
        return new_cls


class LibraryModel(with_metaclass(LibraryModelBase, Node)):
    pass

class Library(LibraryModel):
"""

from peewee import FieldAccessor
class MetadataAccessor(FieldAccessor):

    def __set__(self, instance, value):
        if self.name in instance.__data__:
            raise a
        instance.__data__[self.name] = value
        instance._dirty.add(self.name)


def valid_email_address(email):
    return True

def valid_permissions(value):
    return (True, ["read", "write", "admin"])

class Permissions(dict):
    def __init__(self, library):
        self.library = library
        return None

    def __setitem__(self, item, value):
        if not valid_email_address(item):
            raise ValueError(f"Invalid email address '{item}'")
        
        is_valid, valid_values = valid_permissions(value)
        if not is_valid:
            raise ValueError(f"Invalid permissions among '{value}': must contain only {valid_values}")
        
        self.library._update_permissions(item, value)
        if not value:
            self.__delitem__(item)
        else:
            super().__setitem__(item, value)

    def __delitem__(self, item):
        if self[item]:
            self.library._update_permissions(item, None)
        super().__delitem__(item)


class Library(Model):

    class Meta:
        database = ADSAPI()

    # Immutable:
    _id = TextField(help_text="Unique identifier for this library, which is assigned by ADS.", column_name="id", primary_key=True)

    # Mutable by user:
    _name = TextField(help_text="Given name to the library.")
    _description = TextField(help_text="Description of the library.")
    _public = BooleanField(help_text="Whether the library is public.")
    _owner = TextField(help_text="Owner of the library.")
    _permissions = TextField(help_text="Permission level of the library.")

    # Mutable locally, but has no impact on server.
    num_users = IntegerField(help_text="Number of users of the library.")
    num_documents = IntegerField(help_text="Number of documents in the library.")
    date_created = DateTimeField(help_text="Date the library was created.")
    date_last_modified = DateTimeField(help_text="Date the library was last modified.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__data__["permissions"] = Permissions(self)


    def refresh(self):
        with Client() as client:
            # The pagination for documents in a library is a bit weird. Normally the /search/query
            # end point would limit us to 20 results per page (if you believe the documentation,
            # but for my token I have found that to be 200 results per page). But for this library
            # end point, I have tested up to 500 results and seen no pagination.
            # TODO: Ask the ADS team what pagination settings are in place for this end point.
            #       Then make sure that our client will paginate them correctly.
            response = client.api_request(
                f"biblib/libraries/{self.id}", 
                params=dict(rows=self.num_documents)
            )

            # Update the metadata.
            self.__data__.update(response.json["metadata"])
                    
            # The list in `response.json["solr"]["response"]["docs"]` gives bibcodes and alternate
            # bibcodes, but we only need the bibcode and we actually want many other fields.
            # We will store `bibcodes` so we can do operations (e.g., add, remove, etc.) on the 
            # library without ever having to retrieve details about all the documents.

            # Update the bibcodes.
            self.__data__["bibcodes"] = response.json["documents"]

            return response

    def refresh_permissions(self):
        with Client() as client:
            response = client.api_request(f"biblib/permissions/{self.id}")
        self.__data__["permissions"].update(dict(ChainMap(*response.json)))
        return response



    @hybrid_property
    @requires_bibcodes
    def documents(self):
        """ Return the documents in this library as a `DocumentSelect` object. """
        try:
            return self._documents
        except AttributeError:
            print(f"Creating a new DocumentSelect with {len(self.__data__['bibcodes'])} bibcodes")
            self._documents = Document.select()\
                                      .where(
                                          Document.bibcode.in_(self.__data__["bibcodes"])
                                      )\
                                      .limit(self.num_documents)
        finally:
            return self._documents


    @documents.setter
    def documents(self, new_documents):
        """
        Update the documents in this library.

        :param new_documents:
            The new documents to set for this library. This can be an iterable of :class:`ads.Document` objects,
            or an expression that is compatible with :class:`ads.models.document.DocumentSelect`.
        """
        print(f"setting {new_documents}")
        raise a

    @hybrid_property
    def id(self):
        return self._id

    @id.setter
    def id(self, new_id):
        if "_id" in self.__data__:
            raise a
        self.__data__["_id"] = new_id
        return None

    @hybrid_property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, new_name):
        return self._update_metadata("name", new_name)
    
    @hybrid_property
    def description(self):
        return self._description
    
    @description.setter
    def description(self, new_description):
        return self._update_metadata("description", new_description)

    @hybrid_property
    def public(self):
        return self._public
    
    @public.setter
    def public(self, new_public):
        return self._update_metadata("public", bool(new_public))
    
    @hybrid_property
    def owner(self):
        return self._owner
    
    @owner.setter
    def owner(self, email):
        with Client() as client:
            # We need an email address to transfer ownership, but the `owner` string is the ADS
            # username, which is different. So if we don't add ourselves with read permissions 
            # first, we won't be able to access the library after this point.

            # As it turns out, you can't change your own permissions.
            # That means if you wanted to keep read permission after transferring the library
            # you'd have to do something like this:
            
            # Original owner: A
            # New owner: B
            # Extra account managed by A: C

            # A sets C with admin permissions
            # A transfers to B
            # C gives admin (or read/write) permissions to A
            # Can C then even delete themselves as an admin? I don't think so..

            client.api_request(
                f"biblib/transfer/{self.id}",
                data=json.dumps(dict(email=email)),
                method="post"
            )

        # Best we can do is set the new owner's email address.
        self.__data__["_owner"] = email
        return None

    @hybrid_property
    def permissions(self):
        try:
            return self.__data__["permissions"]
        except KeyError:
            self.__data__["permissions"] = Permissions(self)
            self.refresh_permissions()
        finally:
            return self.__data__["permissions"]
        
    @permissions.setter
    def permissions(self, new_permissions):
        # Only apply differences.
        missing_keys = set(self.permissions.keys()).difference(set(new_permissions.keys()))
        for key, value in new_permissions.items():
            if key not in self.permissions or self.permissions[key] != value:
                self.permissions[key] = value
        for key in missing_keys:
            del self.permissions[key]
    
        return None

    def _update_permissions(self, email, new=None):
        _, values = valid_permissions(None)
        permission = { value: False for value in values }
        if new:
            permission.update(dict(zip(new, [True] * len(new))))

        with Client() as client:
            client.api_request(
                f"biblib/permissions/{self.id}",
                data=json.dumps(dict(email=email, permission=permission)),
                method="post"
            )
        return None

    def _update_metadata(self, name, value):
        proxy_name = f"_{name}"
        if proxy_name in self.__data__:
            data = {name: value}

            with Client() as client:
                client.api_request(
                    f"biblib/documents/{self.id}",
                    data=json.dumps(data),
                    method="put"
                )
                
            self.date_last_modified = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')
                        
        else:
            self.__data__[proxy_name] = value
        return None    

    @documents.deleter
    def documents(self):
        """ Delete all documents from a library. """
        return self.empty()

    # Iterating and slicing.

    def __iter__(self):
        yield from self.documents

    def __getitem__(self, index):
        return self.documents[index]

    def append(self, document):
        self._add(document)
        return None
        
    def extend(self, documents):
        self._add(documents)
        return None

    @requires_bibcodes
    def pop(self, index=-1):
        document = self.documents[index]
        self._remove(document)
        return document

    def remove(self, document):
        self._remove(document)
        return None

    def delete(self):
        """ 
        Delete this library.
        
        The :class:`ads.Library` object will continue to persist locally, but it will
        be deleted on the ADS servers.
        """
        with Client() as client:
            # I assumed that this endpoint would be biblib/libraries/{id},
            # but it is actually biblib/documents/{id}. I don't know why.
            # The documentation correctly says biblib/documents/{id}, but
            # the naming convention is not what I expected.
            # TODO: Email ADS team about this.
            #f"biblib/libraries/{self.id}",
            self.api_request(f"biblib/documents/{self.id}", method="delete")
        return True

    def union(self, *libraries):
        """
        Return a new library that is the union of this library and the others.

        :param libraries:
            An iterable of libraries to union with this library.
        
        :returns:
            A new library that is the union of this library and the others.
        """
        response = self._operation("union", libraries)
        return self.__class__(**response.json)

    def intersection(self, library):
        """
        Take the intersection of this library with another.

        :param libraries:
            A list of libraries to take the intersection with this library.
        
        :returns:
            A new library that is the intersection of this library and the other.
        """
        response = self._operation("intersection", [library])
        return self.__class__(**response.json)
    
    def difference(self, library):
        """
        Take the difference of two libraries.

        :param library:
            The library to take the difference with.
        
        :returns:
            A new library that is the difference of this library and the other.
        """
        response = self._operation("difference", [library])
        return self.__class__(**response.json)

    def copy(self, library):
        """
        Copy the bibcode contents from the this library to the given library.
        
        This will not empty the first library.

        :param library:
            The library to copy to.

        :returns:
            A boolean.
        """
        self._operation("copy", [library])
        return None

    def empty(self):
        """ Empty a library of all its documents. """
        self._operation("empty")
        self.__data__["bibcodes"] = []
        try:
            del self._documents
        except AttributeError:
            pass
        return None

    
    @requires_bibcodes
    def _add(self, documents):
        
        # Check if there are any new documents to add.
        documents = flatten(documents)
        existing_bibcodes = self.__data__["bibcodes"]
        new_documents = [doc for doc in documents if doc.bibcode not in existing_bibcodes]
        if not new_documents:
            return dict(number_added=0)

        with Client() as client:
            response = client.api_request(
                f"biblib/documents/{self.id}",
                data=json.dumps(dict(action="add", bibcode=to_bibcode(new_documents))),
                method="post"
            )

        assert response.json["number_added"] == len(new_documents)

        # Update the local store.
        self.__data__["bibcodes"].extend(to_bibcode(new_documents))

        try:
            self._documents
        except AttributeError:
            # No existing DocumentSelect object; nothing to do.
            pass
        else:
            if self._documents._count is None:
                # The DocumentSelect object has not been queried yet; we can just reset it.
                del self._documents
            else:
                # The DocumentSelect object has been queried. We need to update it.
                # This is not a particularly `nice` way to do things, but it avoids additional queries.
                buffer = self._documents._buffer + new_documents
                del self._documents
                
                # Create a new DocumentSelect object.
                self.documents

                # Update the buffer and count.
                self._documents._buffer = buffer
                self._documents._count = len(buffer)
                self._documents._retrieved = len(buffer)

        # Print the current time in full datetime format.
        self.num_documents += response.json["number_added"]
        
        # Update the approx last modified.
        self.date_last_modified = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')
        return response.json


    @requires_bibcodes
    def _remove(self, documents):
        documents = flatten(documents)
        existing_bibcodes = self.__data__["bibcodes"]

        remove_documents = [doc for doc in documents if doc.bibcode in existing_bibcodes]
        if not remove_documents:
            return dict(number_removed=0)

        with Client() as client:
            response = client.api_request(
                f"biblib/documents/{self.id}",
                data=json.dumps(dict(action="remove", bibcode=to_bibcode(remove_documents))),
                method="post"
            )

        # Update the local store.
        # We could use a set for this, but I'd prefer to keep the order of the bibcodes.
        self.__data__["bibcodes"] = [bibcode for bibcode in existing_bibcodes if bibcode not in to_bibcode(remove_documents)]

        try:
            self._documents
        except AttributeError:
            # No existing DocumentSelect object; nothing to do;
            pass
        else:
            if self._documents._count is None:
                # The DocumentSelect object has not been queried yet; we can just reset it.
                del self._documents
            else:
                # The DocumentSelect object has been queried. We need to update it.
                # This is not a particularly `nice` way to do things, but it avoids additional queries.
                buffer = [document for document in self._documents._buffer if document not in remove_documents]
                del self._documents
                
                # Create a new DocumentSelect object.
                self.documents

                # Update the buffer and count.
                self._documents._buffer = buffer
                self._documents._count = len(buffer)
                self._documents._retrieved = len(buffer)

        self.num_documents -= response.json["number_removed"]
        self.date_last_modified = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')
        return response.json

    def _operation(self, action, libraries=None):
        """
        Perform set operations on one or more libraries.

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
            return client.api_request(
                f"biblib/libraries/operations/{self.id}",
                data=json.dumps(payload),
                method="post",
            )


    @classmethod
    def create(cls, name=None, description=None, public=False, documents=None, **kwargs):
        inst = cls(
            name=name,
            description=description,
            public=public,
        )
        raise a
        #inst.save(force_insert=True)
        return inst

    @classmethod
    def select(cls, *fields):
        is_default = not fields
        if not fields:
            fields = cls._meta.sorted_fields
        return LibrarySelect(cls, fields, is_default=is_default)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"<Library {self.id}: {self.name} ({self.num_documents} documents)>"
            
    


class LibrarySelect(Client, ModelSelect):

    def __sql__(self, ctx):
        return ctx.sql(self._where)

    def __str__(self):
        raise a

    
    def execute(self, database=None):
        with self:
            response = self.api_request("biblib/libraries")
        return [Library(**kwds) for kwds in response.json["libraries"]]


