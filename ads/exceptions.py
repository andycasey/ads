"""
Custom exceptions
"""


class APIResponseError(Exception):
    """
    Raised on a HTTP error from the API
    """
    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return repr(self.value)


class SolrResponseParseError(Exception):
    """
    Raised when solr returns an error
    """
    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return repr(self.value)