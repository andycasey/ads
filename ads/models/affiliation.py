"""
Affiliation data model.
"""
from peewee import (TextField, ForeignKeyField, ForeignKeyAccessor)

from ads.models.local import LocalModel

class Affiliation(LocalModel):

    """A data model representing a recognized affiliation parsed by ADS."""

    #: The unique (child) identifier for the affiliation.
    id = TextField(help_text="The unique (child) identifier for the affiliation.")
    #: A foreign key field to any parent identifiers for this affiliation.
    parent = ForeignKeyField("self", backref="children", null=True, help_text="A foreign key field to any parent identifiers for this affiliation.")

    #: The abbreviated affiliation name.
    abbreviation = TextField(help_text="The abbreviated affiliation name.")
    #: The full affiliation name.
    canonical_name = TextField(help_text="The full affiliation name.")
    #: The name of the country that the affiliation is located in.
    country = TextField(help_text="The name of the country that the affiliation is located in.", null=True)

    # See https://github.com/coleifer/peewee/issues/270
    #class Meta:
    #    primary_key = CompositeKey("id", "parent")

    @property
    def parents(self):
        """ Return all possible parents of this affiliation. """
        Parent = self.alias()
        return Parent.select()\
                   .join(Affiliation, on=(Affiliation.parent == Parent.id))\
                   .where(Affiliation.id == self.id)

    @property
    def siblings(self):
        """ Return affiliations that share the same parent as this record. """
        return Affiliation.select().where(Affiliation.parent == self.parent)
    
    @property
    def extended_siblings(self):
        """ Return affiliations that share any parent that is shared by this record. """
        return Affiliation.select().where(Affiliation.parent.in_(list(self.parents)))

    def __repr__(self):
        return f"<Affiliation {self.id}: {self.canonical_name}>"
        

def _safe_get_affiliation(aff_id):
    if aff_id.strip() == "-":
        return None
    return Affiliation.get(id=aff_id.strip())


class AffiliationKeyAccessor(ForeignKeyAccessor):

    def get_rel_instance(self, instance):
        try:
            return instance._affiliation
        except AttributeError:
            _affiliation = []
            for aff_id in instance.aff_id:
                if "; " in aff_id:
                    _affiliation.append(tuple(map(_safe_get_affiliation, aff_id.split("; "))))
                else:
                    _affiliation.append(_safe_get_affiliation(aff_id))
            instance._affiliation = _affiliation
        finally:
            return instance._affiliation


class AffiliationField(ForeignKeyField):
    accessor_class = AffiliationKeyAccessor