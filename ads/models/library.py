"""
Library data model.
"""

from inspect import Attribute
from datetime import datetime
from collections import ChainMap
import json
import re
from peewee import (
    ModelDelete, ModelSelect, Expression, Model, BooleanField, TextField as TextField, IntegerField, DateTimeField,
    SqliteDatabase, Proxy
)
from ads.models.document import Document
from ads.models.utils import hybrid_property
from ads.services.library import (LibraryInterface, Permissions, requires_bibcodes)
from ads.client import Client
from ads.utils import (flatten, to_bibcode)



class Library(Model):

    """
    An object relational mapper for a curated ADS library. 
    """

    #: Unique identifier for this library, which is assigned by ADS.
    id = TextField(help_text="Unique identifier for this library, which is assigned by ADS.", primary_key=True) 
    #: Number of users of the library.
    num_users = IntegerField(help_text="Number of users of the library.")
    #: Number of documents in the library.
    num_documents = IntegerField(help_text="Number of documents in the library.")
    #: Date (UTC) the library was created.
    date_created = DateTimeField(help_text="Date (UTC) the library was created.")
    #: Date (UTC) the library was last modified.
    date_last_modified = DateTimeField(help_text="Date (UTC) the library was last modified.")

    #: Given name to the library.
    name = TextField(help_text="Given name to the library.")
    #: Description of the library.
    description = TextField(help_text="Description of the library.")
    #: Whether the library is public.
    public = BooleanField(help_text="Whether the library is public.")
    #: The ADS username of the owner of the library.
    owner = TextField(help_text="The ADS username of the owner of the library.")

    class Meta:
        database = LibraryInterface(None)
        only_save_dirty = True

    @hybrid_property
    def permissions(self) -> Permissions:
        """
        Permissions set for this library.

        Returns an :class:`ads.models.library.Permissions` object, which inherits from :class:`dict`.
        The keys are the email addresses of the users, and the values are a list of their permissions.
        """
        try:
            return self.__data__["permissions"]
        except KeyError:
            permissions = self.__data__["permissions"] = Permissions(self)
            permissions.refresh()
            return permissions
        except TypeError:
            return None
        
    @permissions.setter
    def permissions(self, permissions):
        # Only apply differences.
        missing_keys = set(self.permissions.keys()).difference(set(permissions.keys()))
        for key, value in permissions.items():
            if key not in self.permissions or self.permissions[key] != value:
                self.permissions[key] = value
        for key in missing_keys:
            del self.permissions[key]    
        return None


    @hybrid_property
    @requires_bibcodes
    def documents(self):
        """ Return the documents in this library as a `DocumentSelect` object. """
        try:
            return self._documents
        except AttributeError:
            print(f"Creating a new DocumentSelect with {len(self.__data__['bibcodes'])} bibcodes")
            self._documents = \
                Document.select()\
                        .where(Document.bibcode.in_(self.__data__["bibcodes"]))\
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
        if "bibcodes" in self.__data__:
            raise NotImplementedError()
        
        bibcodes = [(doc.bibcode if isinstance(doc, Document) else doc) for doc in new_documents]
        self.__data__["bibcodes"] = bibcodes
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
        """ Delete this library from ADS. """
        return super().delete().where(Library.id == self.id).execute()

    def union(self, *libraries):
        """
        Return a new library that is the union of this library and the others.

        :param libraries:
            An iterable of libraries to union with this library.
        
        :returns:
            A new library that is the union of this library and the others.
        """
        return self._operation("union", libraries, return_new_library=True)

    def intersection(self, library):
        """
        Take the intersection of this library with another.

        :param libraries:
            A list of libraries to take the intersection with this library.
        
        :returns:
            A new library that is the intersection of this library and the other.
        """
        return self._operation("intersection", [library], return_new_library=True)
    
    def difference(self, library):
        """
        Take the difference of two libraries.

        :param library:
            The library to take the difference with.
        
        :returns:
            A new library that is the difference of this library and the other.
        """
        return self._operation("difference", [library], return_new_library=True)

    def copy(self, library):
        """
        Copy the bibcode contents from the this library to the given library.
        
        This will not empty the first library.

        :param library:
            The library to copy to.

        :returns:
            A boolean.
        """
        # Should do this locally.
        raise NotImplementedError()
        #return self._operation("copy", [library])

    def empty(self):
        """ Empty a library of all its documents. """
        return self._operation("empty")

    
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

    def _operation(self, action, libraries=None, return_new_library=False):
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
            response = client.api_request(
                f"biblib/libraries/operations/{self.id}",
                data=json.dumps(payload),
                method="post",
            )

        if return_new_library:
            new = self.__class__(**response.json)
            new._dirty.clear()
            return new
        return None


    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"<Library {self.id}: {self.name} ({self.num_documents} documents)>"
            
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
            metadata = response.json["metadata"]
            self.__data__.update(metadata)
            self._dirty -= set(metadata)

            # The list in `response.json["solr"]["response"]["docs"]` gives bibcodes and alternate
            # bibcodes, but we only need the bibcode and we actually want many other fields.
            # We will store `bibcodes` so we can do operations (e.g., add, remove, etc.) on the 
            # library without ever having to retrieve details about all the documents.

            # Update the bibcodes.
            self.__data__["bibcodes"] = response.json["documents"]
            print(f"set bibcodes/documents as not _dirty, and update self._documents if needed")
            return response


