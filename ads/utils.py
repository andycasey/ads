"""
Utilities and helpers
"""

import warnings

from werkzeug._internal import _missing
from werkzeug.utils import cached_property as _cached_property


class cached_property(_cached_property):
    """
    Wrap cached property to print relevant warnings
    """

    def __init__(self, func, name=None, doc=None):
        super(cached_property, self).__init__(func, name, doc)

    def __get__(self, obj, type=None):
        # Essentially copying to insert a message....:
        # https://github.com/pallets/werkzeug/blob/master/werkzeug/utils.py

        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            # One time warning that the user is using lazy loading
            try:
                name = self.func.__name__
            except AttributeError:
                # for python versions at least >= 3.9.6
                name = self.fget.__name__
            warnings.warn(
                "You are lazy loading attributes via '{}', and so are "
                "making multiple calls to the API. This will impact your overall "
                "rate limits.".format(name),
                UserWarning,
            )

            try:
                value = self.func(obj)
            except AttributeError:
                # for python versions at least >= 3.9.6
                value = self.fget(obj)
            obj.__dict__[self.__name__] = value
        return value
