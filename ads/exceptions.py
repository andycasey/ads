"""
Custom exceptions
"""

class APIResponseError(Exception):
    """ An exception that is raised when the ADS API returns an error. """
    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return repr(self.value)