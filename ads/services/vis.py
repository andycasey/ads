
""" A service for visualising data from NASA/ADS. """

import json
from ads.client import Client
from ads.utils import flatten, to_bibcode

# TODO: doc api apges for vizualizations has 'returns author network data' twice instead of author-network and paper network
# Email the ADS team about this.

def author_network(*iterable):
    """
    Generate an author network visualisation given an input set of documents, libraries, or bibcodes.

    :param iterable:
        An iterable of documents, libraries, or bibcodes.
    
    :returns:
        The data for the author network visualisation.
    """        

    # All other ADS endpoints always refer to `bibcode` to mean an array of bibcodes. But if you give `bibcode` here (as the API docs say)
    # then you get an APIResponseError. But here https://github.com/adsabs/vis-services/blob/master/vis_services/views.py#L21
    # you can see it wants `bibcodes` or `query`. Then it works!
    # Email the ADS team about this.

    # TODO: Run author_network using a query instead of a set of bibcodes?

    # Note that from here https://github.com/adsabs/vis-services/blob/master/vis_services/views.py#L19 we can
    # see that this service uses BigQuery
    return _network_request("author", *iterable).json["data"]


def paper_network(*iterable):
    """
    Generate a paper network visualisation given an input set of documents, libraries, or bibcodes.

    :param iterable:
        An iterable of documents, libraries, or bibcodes.
    
    :returns:
        The data for the paper network visualisation.
    """    

    # TODO: Run paper_network using a query instead of a set of bibcodes?
    return _network_request("paper", *iterable).json["data"]


def _network_request(kind, *iterable):
    if kind not in ("paper", "author"):
        raise ValueError(f"Network kind must be either 'paper' or 'author'.")
    bibcodes = flatten(to_bibcode(iterable))
    with Client() as client:
        response = client.api_request(
            f"/vis/{kind}-network",
            method="post",
            data=json.dumps(dict(bibcodes=bibcodes))
        )
    return response
    
