""" Lazily load fields for ``ads.Document`` objects. """

import warnings

from ads.exceptions import APIResponseError

from peewee import (
    Expression,
    OP,
    TextField as _TextField, 
    IntegerField as _IntegerField, 
    DateTimeField as _DateTimeField,
    DateField as _DateField
)

OP.EX = "==" # exact

class LazyAttributesWarning(UserWarning):
    pass


class LazyLibraryFieldAccessor:

    def __init__(self, model, field, name):
        self.model = model
        self.field = field
        self.name = name

    def __set__(self, instance, value):
        instance.__data__[self.name] = value
        instance._dirty.add(self.name)

    def __get__(self, instance, instance_type=None):
        raise a

class LazyDocumentFieldAccessor:

    def __init__(self, model, field, name):
        self.model = model
        self.field = field
        self.name = name


    def __get__(self, instance, instance_type=None):
        if instance is not None:
            if self.name in instance.__data__:
                return instance.__data__[self.name]

            # Lazily-load.
            try:
                key, value = instance._unique_identifier()
            except ValueError:
                raise APIResponseError("Cannot query for a field without an unique identifier (e.g., `id`)")

            warning = (
                "You're lazily loading document attributes, which makes many calls to the "
                "API. This will impact your rate limits. If you know what document fields "
                "you want ahead of time, provide them as arguments to `Document.select()`."
            )
            warnings.warn(warning, category=LazyAttributesWarning)
            # This is a hack to prevent repeated warnings in IPython.
            # See https://github.com/ipython/ipython/issues/11207
            warnings.simplefilter("ignore", category=LazyAttributesWarning)
            
            # TODO: Raise this with the ADS team:
            #       If I do '=bibcode:2005ApJ...622..759G', I get no matches. Here are some weird results:
            #       bibcode:"2005ApJ...622..759G" -> 1 match
            #       =bibcode:"2005ApJ...622..759G" -> 0 match
            #       bibcode:(2005ApJ...622..759G) -> 1 match
            #       =bibcode:(2005ApJ...622..759G) -> 0 match

            from ads.models.document import Document
            query = Document.select(getattr(Document, self.name))\
                            .where(key == value)\
                            .limit(1)
            document, = query

            # If ADS did not send us back the field, then we are going to populate the __data__
            # dictionary with None to avoid infinite loops.
            instance.__data__[self.name] = document.__data__.get(self.name, None)
            return instance.__data__[self.name]

        return self.field

    def __set__(self, instance, value):
        instance.__data__[self.name] = value
        instance._dirty.add(self.name)


class LazyDocumentField:
    accessor_class = LazyDocumentFieldAccessor

class LazyLibraryField:
    accessor_class = LazyLibraryFieldAccessor

class LibraryIntegerField(LazyLibraryField, _IntegerField):
    pass
class LibraryTextField(LazyLibraryField, _TextField):
    pass
class LibraryDateTimeField(LazyLibraryField, _DateTimeField):
    pass

class LibraryDateField(LazyLibraryField, _DateField):
    pass


class TextField(LazyDocumentField, _TextField):

    def exact(self, value):
        return Expression(self, OP.EX, value)

class IntegerField(LazyDocumentField, _IntegerField):
    pass

class DateTimeField(LazyDocumentField, _DateTimeField):
    pass

class DateField(LazyDocumentField, _DateField):
    pass
