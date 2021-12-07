"""
Library data model.
"""

from peewee import (ModelSelect, Expression, Model, BooleanField, TextField, IntegerField, DateField)
from ads.models.base import ADSAPI

class Library(Model):

    class Meta:
        database = ADSAPI()

    name = TextField(help_text="Given name to the library.")
    id = TextField(help_text="Unique identifier for this library, which is assigned by ADS.")
    description = TextField(help_text="Description of the library.")
    public = BooleanField(help_text="Whether the library is public.")

    owner = TextField(help_text="Owner of the library.")
    num_users = IntegerField(help_text="Number of users of the library.")

    date_created = DateField(help_text="Date the library was created.")
    date_last_modified = DateField(help_text="Date the library was last modified.")

    permission = TextField(help_text="Permission level of the library.")

    # num_users

    def append(self, document):
        ...

    def extend(self, documents):
        ...

    def pop(self, index=-1):
        ...

    def remove(self, document):
        ...

    def delete(self):
        ...

    def union(self, *libraries):
        ...

    def intersection(self, library):
        ...

    def difference(self, library):
        ...

    def copy(self, library):
        ...

    def empty(self):
        ...
    


class LibrarySelect(ModelSelect):

    def __sql__(self, ctx):
        return ctx.sql(self._where)

    def __str__(self):
        raise a