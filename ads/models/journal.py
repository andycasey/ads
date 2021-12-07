"""
Journal data model.
"""
from peewee import (TextField, Field, ForeignKeyAccessor, ForeignKeyField)

from ads.models.local import LocalModel
from ads.utils import parse_bibcode

class Journal(LocalModel):

    """ A journal produced by a publisher. """

    abbreviation = TextField(primary_key=True) 
    title = TextField()


class JournalKeyAccessor(ForeignKeyAccessor):
    def get_rel_instance(self, instance):
        # TODO: Need to consider the case where the user is looking for ApJL articles.
        #       There is no specific `Journal` with 'ApJL' as it's abbreviation, but the
        #       bibstem:ApJL search will pick up the right thing. To figure out if something
        #       is ApJL or not we would have to use `ads.utils.parse_bibcode` and check if
        #       the `qualifier` key is 'L'.
        #       We should ask the ADS team about this if there are other kind of gotchas like this.
        return Journal.get(abbreviation=parse_bibcode(instance.bibcode)["bibcode"])


class JournalField(ForeignKeyField):
    accessor_class = JournalKeyAccessor