
import json
from functools import cached_property

from ads import base
from ads.document import Document

class Library(base.BaseQuery):

    def __init__(self, documents=None, name=None, description=None, public=False, **kwargs):
        """
        A library object.

        :param documents: [optional]
            Optionally supply documents (or a list of bibcodes) to add to this new library.

        :param name: [optional]
            The name for this library. If `None` is given it will default to 'Unnamed Library <X>',
            where `X` is the next available number.

        :param description: [optional]
            A short description for this library.
        
        :param public: [optional]
            Whether or not this library is public (default: False).
        """
        
        library_id = kwargs.get("id", None)
        if library_id is None:
            # New library, create it remotely.
            metadata = self._create(
                name=name, 
                description=description,
                public=public, 
                documents=documents,
                **kwargs
            )
            self.id = metadata["id"]
            self._name = metadata["name"]
            self._description = metadata["description"]

            self._documents = _to_document(documents)
            self._num_documents = len(set(documents))
            self._num_users = 1

            # If we want other information, we need to do a refresh.            
            # Owner
            # date created
            # date last modified

        else:
            assert documents is None
            # Existing library that has been fetched from the server.
            self.id = library_id
            self._date_created = kwargs.get("date_created", None)
            self._date_last_modified = kwargs.get("date_last_modified", None)
            self._owner = kwargs.get("owner", None)
            self._num_documents = kwargs.get("num_documents", None)
            self._num_users = kwargs.get("num_users", None)

            # If this is a new library that has been set from an operation, then we will have the bibcodes.
            if "bibcodes" in kwargs:
                self._documents = _to_document(kwargs["bibcodes"])
            # TODO: permission

        # We use private attribute because we will use setters/getters for this.
        self._name = name
        self._description = description
        self._public = public

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.name}' ({self.id})>"

    @property
    def name(self):
        """ The name of this library. """
        return self._name

    @name.setter
    def name(self, name):
        """ Update the name of this library. """
        if name != self._name:
            self.update_metadata(name=name)
        return None

    @property
    def description(self):
        """ A short description for this library. """
        return self._description
    
    @description.setter
    def description(self, description):
        """ Update the description for this library. """
        if description != self._description:
            self.update_metadata(description=description)
        return None

    @property
    def public(self):
        """ Whether this library is publicly accessible or not. """
        return self._public
    
    @public.setter
    def public(self, value):
        """ Update permissions on whether this library is publicly accessible."""
        value = bool(value)
        if value != self._public:
            self.update_metadata(public=value)
        return None

    @property
    def date_created(self):
        """ The UTC date the library was created. """
        return self._date_created
    
    @property
    def date_last_modified(self):
        """ The UTC date the library was last modified. """
        return self._date_last_modified

    @property
    def owner(self):
        """ The ADS username of the owner of this library. """
        return self._owner
    
    @property
    def num_documents(self):
        """ The number of documents in this library. """
        return self._num_documents
    
    @property
    def num_users(self):
        """ The number of users of this library. """
        return self._num_users


    def _create(self, name=None, description=None, public=False, documents=None, **kwargs):
        """
        Execute an API request to create a library for the user.
        """
        payload = dict(public=bool(public))
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if documents:
            payload["bibcode"] = _to_bibcode(documents)
            
        response = self.api_request(
            f"biblib/libraries",
            method="post",
            data=json.dumps(payload),
            **kwargs
        )
        metadata = response.json
        return metadata

    @cached_property
    def documents(self):
        try:
            return self._documents
        except AttributeError:
            self.refresh()
            # TODO: .refresh will just get us the bibcodes, but we need to use BigQuery to get
            # information about the actual documents.
        finally:
            return self._documents

    def __iter__(self):
        yield from self.documents

    def __getitem__(self, index):
        return self.documents[index]
        
    def refresh(self):
        """ 
        Refresh all properties (documents, permissions, metadata) from the ADS server. 
        
        This should only be necessary if you are making simultaneous changes to the library
        through the ADS web interface.
        """
        # Interestingly, we need to supply the number of documents we want back from this
        # end point, even though it's not documented. Otherwise we just get 20 rows back.
        # TODO: Create a library with more than 2,000 documents (or whatever max_rows is)
        #       and do the pagination automagically.
        # TODO: Email ADS team about this.
        response = self.api_request(
            f"biblib/libraries/{self.id}", 
            params=dict(rows=self.num_documents or 2_000)
        )
        self._documents = _to_document(response.json["documents"])
        return response

    def append(self, document):
        """
        Append a document to this library.
        
        :param document:
            The document to add to this library.
        """
        self._add([document])
        self._documents.append(document)
        return None

    def extend(self, documents):
        """
        Add documents to this library.

        :param documents:
            A list-like of documents (or bibcodes) to add to this library.
        """
        self._add(documents)
        # TODO: What if they are duplicates? Need unit test..
        self._documents.extend(documents)
        return None
    
    def _add(self, documents):
        """
        Make an API request to add documents to the library.
        This private method assumes you will add the document to the local `._documents.
        """
        return self.api_request(
            f"biblib/documents/{self.id}",
            data=json.dumps(dict(action="add", bibcode=[_to_bibcode(documents)])),
            method="post"
        )

    def pop(self, index=-1):
        """
        Remove and return the document at index (default last).
        
        Raises IndexError if the library is empty or index is out of range.
        """
        # Try removing it from remote first.
        self._remove(self._documents[index])
        return self._documents.pop(index)

    def remove(self, document):
        """
        Remove a document from the library.
        """        
        self._remove(document)
        self._documents.remove(document)
        return None

    def _remove(self, document):
        """
        Make an API request to remove a document from the library.
        This private method assumes you will remove the document from the local `._documents`.
        """
        return self.api_request(
            f"biblib/documents/{self.id}",
            data=json.dumps(dict(action="remove", bibcode=[_to_bibcode(document)])),
            method="post",
        )

    def delete(self):
        """ Delete this library. """
        self.api_request(
            # I assumed that this endpoint would be biblib/libraries/{id},
            # but it is actually biblib/documents/{id}. I don't know why.
            # The documentation correctly says biblib/documents/{id}, but
            # the naming convention is not what I expected.
            # TODO: Email ADS team about this.
            #f"biblib/libraries/{self.id}",
            f"biblib/documents/{self.id}",
            method="delete"
        )
        self.__del__()
        return True

    def __del__(self):
        try:
            self.session.close()
        finally:
            return None

    def union(self, *libraries):
        """
        Return a new library that is the union of this library and the others.

        :param libraries:
            A list of libraries to union with this library.
        """
        response = self._operation("union", libraries)
        # Return a new library object
        return self.__class__(**response.json)

    def intersection(self, library):
        """
        Take the intersection of this library with another.

        :param libraries:
            A list of libraries to take the intersection with this library.
        """
        response = self._operation("intersection", [library])
        # Return a new library object
        return self.__class__(**response.json)

    def difference(self, library):
        """
        Take the difference of two libraries
        """
        response = self._operation("difference", [library])
        # Return a new library object
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
        self._documents = []
        return None

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

        return self.api_request(
            f"biblib/libraries/operations/{self.id}",
            data=json.dumps(payload),
            method="post",
        )

    def transfer_ownership(self, email):
        """
        Transfer ownership of this library to another user.
        
        :param email:
            The email address of the new owner.
        """
        self.api_request(
            f"biblib/transfer/{self.id}",
            data=json.dumps(dict(email=email)),
            method="post"
        )
        return None

    def update_permissions(self, email, read=None, write=None, admin=None):
        """
        Update permissions of this library.

        :param email:
            The email address of the user to update permissions for.

        :param read: [optional]
            Whether or not the user should have read permissions.

        :param write: [optional]
            Whether or not the user should have write permissions.

        :param admin: [optional]
            Whether or not the user should have admin permissions.
        
        :returns:
            A boolean indicating whether or not the permissions were updated.
        """
        if all(item is None for item in (read, write, admin)):
            # Nothing to do.
            return False

        permission = dict()
        if read is not None:
            permission["read"] = bool(read)
        if write is not None:
            permission["write"] = bool(write)
        if admin is not None:
            permission["admin"] = bool(admin)

        payload = dict(email=email, permission=permission)
        self.api_request(
            f"biblib/permissions/{self.id}",
            data=json.dumps(payload),
            method="POST"
        )
        # TODO: If we have permissions stored locally, update them.
        return True

    def update_metadata(self, name=None, description=None, public=None):
        """
        Update the metadata of this library.

        :param name: [optional]
            A new name for this library.
        
        :param description: [optional]
            A new description for this library.
        
        :param public: [optional]
            Whether to make this library public or private.
        
        :returns:
            A boolean indicating whether or not the metadata was updated.
        """
        if all(item is None for item in (name, description, public)):
            # Nothing to do.
            return False    
        
        data = dict()
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if public is not None:
            data["public"] = bool(public)

        response = self.api_request(
            f"biblib/documents/{self.id}",
            data=json.dumps(data),
            method="PUT"
        )
        for key in data.keys():
            setattr(self, f"_{key}", response.json[key])
        return True


    @cached_property
    def permissions(self):
        # TODO: Would be nice to have a permissions object so that when changes are made
        # to that dict-like thing, we can update the permissions on the server.
        return self.api_request(f"biblib/permissions/{self.id}").json[0]


def retrieve():
    """ Retrieve all libraries for a given user. """

    with base.BaseQuery() as query:
        response = query.api_request("biblib/libraries")
    return tuple(Library(**kwds) for kwds in response.json["libraries"])
    

def _to_bibcode(bibcode_or_document):
    """ Resolve a bibcode or document to a bibcode. """
    if isinstance(bibcode_or_document, str):
        return bibcode_or_document
    elif isinstance(bibcode_or_document, (tuple, list)):
        return list(map(_to_bibcode, bibcode_or_document))
    else:
        try:
            return bibcode_or_document.bibcode
        except AttributeError:
            raise TypeError(f"Must supply an `ads.Document` or a bibcode string (not {type(bibcode_or_document)}: {bibcode_or_document})")

def _to_document(bibcode_or_document):
    """ Resolve a bibcode or document to a document. """
    if isinstance(bibcode_or_document, Document):
        return bibcode_or_document
    elif isinstance(bibcode_or_document, str):
        return Document(bibcode=bibcode_or_document)
    elif isinstance(bibcode_or_document, (tuple, list)):
        return list(map(_to_document, bibcode_or_document))
    else:
        raise TypeError(f"Unknown document type")