"""
Journal data model.
"""
from peewee import TextField

from ads.models.local import LocalModel


class Journal(LocalModel):

    """ A journal produced by a publisher. """

    abbreviation = TextField(primary_key=True) 
    title = TextField()