"""
Custom exceptions
"""

class SolrResponseParseError(Exception):
    """
    Raised when no signature info is found
    """
    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return repr(self.value)