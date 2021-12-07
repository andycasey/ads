"""
Affiliation data model.
"""
from peewee import (TextField, ForeignKeyField, ForeignKeyAccessor)

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