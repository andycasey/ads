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
    _biblib_url = f"{ADSWS_API_URL}/biblib"
    _libraries_url = f"{_biblib_url}/libraries"
    
    def __init__(self, id: str, **meta):
        self.id = id
        
        self._library_url = f"{self._libraries_url}/{self.id}"
        self._docs_url = f"{self._biblib_url}/documents/{self.id}"
        self._permissions_url = f"{self._biblib_url}/permissions/{self.id}"
        self._ops_url = f"{self._libraries_url}/operations/{self.id}"
        if meta:
            self._meta = meta
        else:
            self._refresh_metadata()
        self._meta_keys = tuple(self._meta.keys())
        
    def _refresh_metadata(self):
        self._meta = self.session.get(self._library_url).json()
    
    def __getattr__(self, item):
        if item in self._meta_keys:
            if item not in self._meta:
                self._refresh_metadata()
            return self._meta[item]
        
        raise AttributeError(f"'{item}' is not an attribute of Library")
        
    def __setattr__(self, item, value):
        if item in ['name', 'description', 'public']:
            self.session.put(self._docs_url, payload=json.dumps({item: value}))
            self._meta[item] = value
            del self._meta['date_last_modified']
            

    def get_documents(self, **kwargs):
        """Return a SearchQuery representing all documents in this library."""
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
        docs = self._to_bibcodes(docs)
        payload = {
            'bibcode': docs,
            'action': 'add'
        }
        
        result = self.session.post(self._docs_url, data=json.dumps(payload))
        
        del self._meta['num_documents']
        del self._meta['date_last_modified']
        return result.json()['number_added']
    
    
    def remove_documents(self, docs) -> int:
        docs = self._to_bibcodes(docs)
                    
        payload = {
            'bibcode': docs,
            'action': 'remove'
        }

        del self._meta['num_documents']
        del self._meta['date_last_modified']     
        result = self.session.post(self._docs_url, data=json.dumps(payload))
        return result.json()['number_removed']
        
    @classmethod
    def new(cls, name=None, description='My ADS Library', public=False, docs=None):
        docs = cls._to_bibcodes(docs)
        
        payload = {'description': description, 'public': public}
        if name:
            payload['name'] = name
            
        if docs:
            payload['docs'] = docs
        
        q = BaseQuery()
        result = q.session.post(cls._libraries_url, data=json.dumps(payload))
        
        return cls(result.json()['id'])
    
    def get_user_permissions(self):
        return self.session.get(self._permissions_url).json()
    
    def edit_user_persmissions(self, email, permission):
        assert [p in 'rwa' for p in permission]

        permission = {
            'read': 'r' in permission,
            'write': 'w' in permission,
            'admin': 'a' in permission            
        }
        
        payload = {'permission': permission, 'email': email}
        res = self.session.post(self._permissions_url, payload=json.dumps(payload))
        
        del self._meta['num_users']
        del self._meta['date_last_modified']
        
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
        if isinstance(libraries, (str, Library)):
            libraries = [libraries]
        
        res = self._set_operations('union', libraries, name=name, description=description, public=public)
        return self.__class__(res['id'])
    
    def difference(self, libraries, name=None, description=None, public=False):
        if isinstance(libraries, (Library, str)):
            libraries = [libraries]
        
        res = self._set_operations('difference', libraries, name=name, description=description, public=public)
        return self.__class__(res['id'])
    
    def intersection(self, libraries, name=None, description=None, public=False):
        if isinstance(libraries, (Library, str)):
            libraries = [libraries]
        
        res = self._set_operations('intersection', libraries, name=name, description=description, public=public)
        return self.__class__(res['id'])
    
    def empty(self):
        del self._meta['num_documents']
        del self._meta['date_last_modified']
        self._set_operations('empty', libraries=[])
        
    def copy_to(self, library):
        library = [library]            
        res = self._set_operations('copy', library)
        return self.__class__(res['id'])
    
    def transfer_to(self, email):
        self.session.post(f"{self._biblib_url}/transfer/{self.id}", payload=json.dumps({'email': email}))
        
    