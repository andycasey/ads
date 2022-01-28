"""
Library data model.
"""
from peewee import (Model, BooleanField, TextField, IntegerField, DateTimeField)
from ads.models.document import Document
from ads.utils import to_bibcode

from ads.services.library import (LibraryInterface, DocumentArrayField, PermissionsField, operation)

from ads import logger

class Library(Model):

    """ A data model for a library managed by ADS. """
    
    # Immutable fields

    #: Unique identifier for this library, which is assigned by ADS.
    id = TextField(help_text="Unique identifier for this library, which is assigned by ADS.", primary_key=True) 
    #: Number of users of the library.
    num_users = IntegerField(help_text="Number of users of the library.")
    #: Number of documents in the library.
    num_documents = IntegerField(help_text="Number of documents in the library.")
    #: Date (UTC) the library was created.
    date_created = DateTimeField(help_text="Date (UTC) the library was created.",)# formats=["%Y-%m-%dT%H:%M:%S.%f"])
    #: Date (UTC) the library was last modified.
    date_last_modified = DateTimeField(help_text="Date (UTC) the library was last modified.",)# formats=["%Y-%m-%dT%H:%M:%S.%f"])

    # Mutable fields

    #: Given name to the library.
    name = TextField(help_text="Given name to the library.")
    #: Description of the library.
    description = TextField(help_text="Description of the library.")
    #: Whether the library is public.
    public = BooleanField(help_text="Whether the library is public.", default=False)
    #: The ADS username of the owner of the library.
    owner = TextField(help_text="The ADS username of the owner of the library.")
    #: The documents in this library.
    documents = DocumentArrayField(Document, lazy_load=True, null=True, help_text="The documents in this library.")
    #: Permissions for the library.
    permissions = PermissionsField("self", backref="children", lazy_load=True, null=True, help_text="Permissions for the library.")

    class Meta:
        database = LibraryInterface(None)
        only_save_dirty = True

    # Iterating and slicing.

    def __iter__(self):
        yield from self.documents

    def __getitem__(self, index):
        return self.documents[index]

    # Set operations.

    def union(self, *libraries):
        """
        Return a new library that is the union of this library and the others.

        :param libraries:
            An iterable of libraries to union with this library.
        
        :returns:
            A new library that is the union of this library and the others.
        """
        return operation(self, "union", libraries, return_new_library=True)

    def intersection(self, library):
        """
        Take the intersection of this library with another.

        :param libraries:
            A list of libraries to take the intersection with this library.
        
        :returns:
            A new library that is the intersection of this library and the other.
        """
        return operation(self, "intersection", [library], return_new_library=True)
    
    def difference(self, library):
        """
        Take the difference of two libraries.

        :param library:
            The library to take the difference with.
        
        :returns:
            A new library that is the difference of this library and the other.
        """
        return operation(self, "difference", [library], return_new_library=True)

    def copy(self, library):
        """
        Copy the bibcode contents from the this library to the given library.
        
        This will not empty the first library.

        :param library:
            The library to copy to.

        :returns:
            A boolean.
        """
        return operation(self, "copy", [library])

    def empty(self):
        """ Empty a library of all its documents. """
        return operation(self, "empty")

    def delete(self):
        """ Delete this library from ADS. """
        return super().delete().where(Library.id == self.id).execute()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"<Library {self.id}: {self.name} ({self.num_documents} documents)>"

    # A little bit of magic to make sure documents and permissions work correctly.
    # Specifically, we have to work out the `diff` changes needed to send to ADS.


    def _populate_unsaved_relations(self, field_dict):
        super()._populate_unsaved_relations(field_dict)

        if "bibcodes" in field_dict:
            del field_dict["bibcodes"]

        if "id" in self.__data__ and ("bibcodes" in self.__data__ or "documents" in self.__data__):
            # We're updating, so we need to take the difference in documents.
            if "bibcodes" in self.__data__ and "documents" not in self.__data__:
                # No changes to be made.
                if "documents" in field_dict:
                    del field_dict["documents"]
            else:
                self.documents # trigger to update bibcodes if we don't have them
                new = list(map(to_bibcode, self.__data__["documents"]))
                old = self.__data__["bibcodes"]
                add, remove = (list(set(new).difference(old)), list(set(old).difference(new)))
                if add or remove:
                    field_dict["documents"] = dict(add=add, remove=remove)
                elif "documents" in field_dict:
                    del field_dict["documents"]


        if "id" in self.__data__ and "permissions" in self._dirty and hasattr(self, "_permissions"):
            old = self.__data__.get("permissions", {})
            new = getattr(self, "_permissions", {})

            field_dict["permissions"] = new
            logger.debug(old)
            logger.debug(new)



        
    # Unlike most attributes where we can just record if they are dirty or not, we need to keep 
    # track of the old and new values of documents and permissions.

    # The .documents attribute must be the new value, and must be a list of Document objects.
    # The __data__["bibcodes"] will reference the old value.


    def save(self, force_insert=False, only=None):
        #print(f"saving {force_insert} {only}")
        self._dirty.update({"documents", "permissions"})
        #self._dirty.remove("bibcodes")
        result = super().save(force_insert=force_insert, only=only)
        # Keep documents in sync.
        if "documents" in self.__data__:
            self.__data__["bibcodes"] = list(map(to_bibcode, self.__data__["documents"]))
            self.__data__["num_documents"] = len(self.__data__["bibcodes"])
        #if getattr(self, "_documents", None) is not None:
        #    self.__data__["num_documents"] = len(self._documents)
        if "permissions" in self.__data__ and hasattr(self, "_permissions"):
            self.__data__["permissions"] = dict(self._permissions)
        
        # Keep documents in sync.
        '''
        if getattr(self, "_documents", None) is not None:
            if all(isinstance(doc, Document) for doc in self._documents):
                self.__data__["documents"] = [doc.bibcode for doc in self._documents]
            elif all(isinstance(doc, str) for doc in self._documents):
                # Bibcodes given. Reset `_documents`
                self.__data__["documents"] = [] + self._documents
                self._documents = None
            else:
                raise ValueError("eek")
        '''
        return result
