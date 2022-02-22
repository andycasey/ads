"""Functions to interact with ADS libraries."""
from .base import BaseQuery
from .config import ADSWS_API_URL
from .search import SearchQuery
import json
import six

class Library(BaseQuery):
    def __init__(self, id: str):
        self.id = id
        
        self._library_url = f"{ADSWS_API_URL}/biblib/libraries/{self.id}"
        self._docs_url = f"{ADSWS_API_URL}/biblib/documents/{self.id}"
        
    def get_documents(self, **kwargs):
        """Return a SearchQuery representing all documents in this library."""
        return SearchQuery(q=f'docs(library/{self.id})', **kwargs) #self.session.get(self._url).json()['documents']


    def add_documents(self, docs) -> int:
        if isinstance(docs, six.string_types):
            docs = [docs]
        else:
            docs = list(docs)
            
        payload = {
            'bibcode': docs,
            'action': 'add'
        }
        
        result = self.session.post(self._docs_url, data=json.dumps(payload))
        print(result)
        return result.json()['number_added']
    
    
    def remove_documents(self, docs) -> int:
        if isinstance(docs, six.string_types):
            docs = [docs]
        else:
            docs = list(docs)
            
        payload = {
            'bibcode': docs,
            'action': 'remove'
        }
        
        result = self.session.post(self._docs_url, data=json.dumps(payload))
        return result.json()['number_removed']
        