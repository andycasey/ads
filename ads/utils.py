"""
Utilities and helpers
"""

import warnings
from werkzeug.utils import cached_property as _cached_property


class cached_property(_cached_property):
    """
    Wrap cached property to print relevant warnings
    """
    def __init__(self, func, name=None, doc=None):
        super(cached_property, self).__init__(func, name, doc)

    def __get__(self, obj, type=None):
        # One time warning that the user is using lazy loading
        warnings.warn(
            "You are lazy loading attributes via '{}', and so are "
            "making multiple calls to the API. This will impact your overall "
            "rate limits."
            .format(self.func.__name__),
            UserWarning,
        )
        return super(cached_property, self).__get__(obj, type)
