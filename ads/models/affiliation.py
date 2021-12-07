"""
Affiliation data model.
"""
from peewee import TextField, ForeignKeyField

from ads.models.local import LocalModel

class Affiliation(LocalModel):

    """A data model representing a recognized affiliation parsed by ADS."""

    id = TextField() # This is the same as `child_id` in the current ADS data model.
    parent = ForeignKeyField("self", backref="children", null=True)

    abbreviation = TextField()
    canonical_name = TextField()
    country = TextField(null=True)

    # See https://github.com/coleifer/peewee/issues/270
    #class Meta:
    #    primary_key = CompositeKey("id", "parent")