
""" Miscellaneous services offered by ADS. """

import json
from ads import Document
from ads.client import Client
from ads.utils import flatten, to_bibcode

def citation_helper(*iterable, as_documents=True):
    """
    Given a set of documents, use a 'friends of friends' analysis to suggest up to ten missing citations.
    These missing citations cite and/or are cited by the documents given, but are not in the list.

    :param iterable:
        An iterable of documents, libraries, or bibcodes.
    
    :param as_documents: [optional]
        If `True`, return a list of suggested documents as :class:`ads.Document` objects (default).        
        Otherwise, return the raw JSON output from ADS.
    """
    # TODO: Should we check if an item is a library, and if so just to use the internal bibcode instead?
    bibcodes = flatten(to_bibcode(iterable))
    with Client() as client:
        response = client.api_request(
            f"/citation_helper",
            method="post",
            data=json.dumps(dict(bibcodes=bibcodes))
        )
    
    if as_documents:
        # TODO: Should we just return Documents with bibcodes and let lazy-loading deal with it?
        missing_bibcodes = [each["bibcode"] for each in response.json]
        return list(Document.select().where(Document.bibcode.in_(missing_bibcodes)))
    else:
        return response.json["data"]