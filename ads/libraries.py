"""Functions to interact with ADS libraries."""
from .base import BaseQuery
from .config import ADSWS_API_URL
from .search import SearchQuery, Article
import json
import six

def delete_library(id: str):
    q = BaseQuery()
    lib = Library(id)
    q.session.delete(lib._docs_url)
    
def get_user_libraries():
    q = BaseQuery()
    out = q.session.get(Library._libraries_url).json()
    return [Library(id=o.pop('id'), **o) for o in out]
    
class Library(BaseQuery):
    """An object representing an ADS library."""
    _biblib_url = f"{ADSWS_API_URL}/biblib"
    _libraries_url = f"{_biblib_url}/libraries"
    
    def __init__(self, id: str, **meta):
        
        self.id = id
        self._library_url = f"{self._libraries_url}/{id}"
        self._docs_url = f"{self._biblib_url}/documents/{id}"
        self._permissions_url = f"{self._biblib_url}/permissions/{id}"
        self._ops_url = f"{self._libraries_url}/operations/{id}"

        if not meta:
            self._refresh_metadata()
        else:
            for key, val in meta.items():
                setattr(self, key, val)
        
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        
        return self.id == other.id
    
    def _refresh_metadata(self):
        meta = self.session.get(self._library_url).json()
        for key, val in meta.items():
            setattr(self, key, val)
                
    def set(self, **items):
        assert all(name in ['name', 'description', 'public'] for name in items)
        self.session.put(self._docs_url, payload=json.dumps(items))
        self._refresh_metadata()

    def get_documents(self, **kwargs):
        """Return a :class:`~search.SearchQuery` representing all documents in this library."""
        return SearchQuery(q=f'docs(library/{self.id})', **kwargs)

    @staticmethod
    def _to_bibcodes(docs):
        if isinstance(docs, six.string_types):
            return [docs]
        
        if not hasattr(docs, '__iter__'):
            raise TypeError("docs must be a str or iterable of strings or Articles")

        out = []
        for d in docs:
            if isinstance(d, six.string_types):
                out.append(d)
            elif isinstance(d, Article):
                out.append(d.bibcode)

        return out        
        
    def add_documents(self, docs) -> int:
        """Add a list of documents to the library.
        
        :param docs: documents to add to the library.
        :type docs: string bibcode, or sequence of string bibcodes, or sequence of 
            :class:`search.Article`
        """
        docs = self._to_bibcodes(docs)
        payload = {
            'bibcode': docs,
            'action': 'add'
        }
        
        result = self.session.post(self._docs_url, data=json.dumps(payload))
        
        self._refresh_metadata()
        return result.json().get('number_added', -1)
    
    
    def remove_documents(self, docs) -> int:
        """Remove a list of documents from the library.
        
        :param docs: documents to remove from the library.
        :type docs: string bibcode, or sequence of string bibcodes, or sequence of 
            :class:`search.Article`
        """
        docs = self._to_bibcodes(docs)
                    
        payload = {
            'bibcode': docs,
            'action': 'remove'
        }

        self._refresh_metadata()  
        result = self.session.post(self._docs_url, data=json.dumps(payload))
        return result.json()['number_removed']
        
    @classmethod
    def new(cls, name=None, description='My ADS Library', public=False, docs=None):
        """Create a new library and return it.
        
        :param name: Name of the library, default "Untitled Library" with incremented
            integer appended.
        :type name: string
        :param description: description of the library.
        :type description: str
        :param public: whether the library should be public
        :type public: bool
        :param docs: documents to add to the library 
        :type docs: string bibcode, or sequence of string bibcodes, or sequence of 
            :class:`search.Article`
        """
        docs = cls._to_bibcodes(docs)
        
        payload = {'description': description, 'public': bool(public)}
        if name:
            payload['name'] = name
            
        if docs:
            payload['docs'] = docs
        
        q = BaseQuery()
        result = q.session.post(cls._libraries_url, data=json.dumps(payload))
        
        return cls(result.json()['id'])
    
    def get_user_permissions(self):
        """Get persmissions of different users."""
        return self.session.get(self._permissions_url).json()
    
    def edit_user_persmissions(self, email, permission):
        """Edit permissions of a user (or add new user).
        
        :param email: email of the (new) user
        :type email: str
        :param permission: the associated permissions to set, should be a string
            containing any combination of 'rwa' (read, write, admin).
        """

        assert [p in 'rwa' for p in permission]

        permission = {
            'read': 'r' in permission,
            'write': 'w' in permission,
            'admin': 'a' in permission            
        }
        
        payload = {'permission': permission, 'email': email}
        res = self.session.post(self._permissions_url, payload=json.dumps(payload))
        
        self._refresh_metadata()
        
        return res.json()['message']
    
    def _set_operations(self, action, libraries, **kwargs):
        kw = {k: v for k, v in kwargs.items() if v is not None}
        payload = {
            'action': action,
            'libraries': [l.id if isinstance(l, Library) else l for l in libraries],
            **kw
        }
        res = self.session.post(self._ops_url, payload = json.dumps(payload))
        return res.json()
        
    def union(self, libraries, name=None, description=None, public=False):
        """Form a new library from the union of this library and other libraries.
        
        Returns the new :class:`Library` object.
        
        :param libraries: libraries to take the union of.
        :type libraries: str identifier, :class:`Library` or sequence of such.
        :param name: Name of the library, default "Untitled Library" with incremented
            integer appended.
        :type name: string
        :param description: description of the library.
        :type description: str
        :param public: whether the library should be public
        :type public: bool
        """    
        if isinstance(libraries, (str, Library)):
            libraries = [libraries]
        
        res = self._set_operations('union', libraries, name=name, description=description, public=public)
        return self.__class__(res['id'])
    
    def difference(self, libraries, name=None, description=None, public=False):
        """Form a new library from the difference of this library and other libraries.
        
        Returns the new :class:`Library` object.
        
        :param libraries: libraries to difference with this one.
        :type libraries: str identifier, :class:`Library` or sequence of such.
        :param name: Name of the library, default "Untitled Library" with incremented
            integer appended.
        :type name: string
        :param description: description of the library.
        :type description: str
        :param public: whether the library should be public
        :type public: bool
        """
        if isinstance(libraries, (Library, str)):
            libraries = [libraries]
        
        res = self._set_operations('difference', libraries, name=name, description=description, public=public)
        return self.__class__(res['id'])
    
    def intersection(self, libraries, name=None, description=None, public=False):
        """Form a new library from the intersection of this library and other libraries.
        
        Returns the new :class:`Library` object.
        
        :param libraries: libraries to take the intersect.
        :type libraries: str identifier, :class:`Library` or sequence of such.
        :param name: Name of the library, default "Untitled Library" with incremented
            integer appended.
        :type name: string
        :param description: description of the library.
        :type description: str
        :param public: whether the library should be public
        :type public: bool
        """
        if isinstance(libraries, (Library, str)):
            libraries = [libraries]
        
        res = self._set_operations('intersection', libraries, name=name, description=description, public=public)
        return self.__class__(res['id'])
    
    def empty(self):
        """Empty this library of all documents."""
        self._set_operations('empty', libraries=[])
        self._refresh_metadata()

    def copy_to(self, library):
        """Copy documents in this library to another library.
        
        :param library: the library to copy to
        :type library: str id or :class:`Library`.
        """
        library = [library]            
        res = self._set_operations('copy', library)
        return self.__class__(res['id'])
    
    def transfer_to(self, email):
        """Transfer the library ownership to another user.
        
        :param email: the email to transfer ownership to.
        """
        self.session.post(f"{self._biblib_url}/transfer/{self.id}", payload=json.dumps({'email': email}))
        self._refresh_metadata()
    