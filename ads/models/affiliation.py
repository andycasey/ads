"""
Affiliation data model.
"""
from peewee import TextField, ForeignKeyField

from ads.models.local import LocalModel


class Country(LocalModel):

    """A country."""

    name = TextField(primary_key=True)


class Affiliation(LocalModel):

    """A data model representing a recognized affiliation parsed by ADS."""

    id = TextField() # This is the same as `child_id` in the current ADS data model.
    parent = ForeignKeyField("self", backref="children", null=True)

    abbreviation = TextField()
    canonical_name = TextField()

    #country = ForeignKeyField(Country, backref="child_affiliations", null=True)
    country = TextField(null=True)

    # See https://github.com/coleifer/peewee/issues/270
    #class Meta:
    #    primary_key = CompositeKey("id", "parent")



if __name__ == "__main__":
    import os

    os.remove("models.db") # for testing.

    from ads.models.local import database

    database.connect()
    database.create_tables([Affiliation, Country])
    database.close()

    # Load in the affiliation DB    
    import os
    from collections import OrderedDict
    _database_path = os.path.expanduser("~/.ads/affiliations.tsv")
    _country_database_path = os.path.expanduser("~/.ads/affiliations_country.tsv")

    countries_dict = OrderedDict()
    with open(_country_database_path, "r") as fp:
        for line in fp.readlines()[1:]:
            country, parent_id, child_id, abbrev, canonical_affiliation = line.split("\t")
            country = country or None

            # affiliations.tsv uses "0" to indicate no ID, but affiliations_country.tsv uses ""
            parent_id, child_id = (parent_id or "0", child_id or "0")

            key = f"{parent_id}|{child_id}"
            countries_dict[key] = [country, parent_id, child_id, abbrev, canonical_affiliation]

            try:
                with database.atomic():
                    Country.create(name=country)
            except:
                None


    with open(_database_path, "r") as fp:
        for line in fp.readlines()[1:]:
            parent_id, child_id, abbreviation, canonical_name = line.strip().split("\t")
            
            # Resolve the country with this method order
            # 1. Match by parent_id and child_id.
            # 2. Match by child_id.
            # 3. Match by parent_id.
            keys = (f"{parent_id}|{child_id}", f"|{child_id}", f"{parent_id}|")
            for key in keys:
                try:
                    country_info = countries_dict[key]
                except KeyError:
                    continue
                else:
                    country = country_info[0]#Country(name=country_info[0])
                    break
            else:
                country = None
            
            if parent_id == "0":
                parent = None

            else:
                parent = Affiliation(id=parent_id)

            Affiliation.create(
                id=child_id,
                abbreviation=abbreviation,
                canonical_name=canonical_name,
                country=country,
                parent=parent
            )

    """
    author = Author(name="Casey, A")
    affiliations = (Affiliation(id="A00268"), Affiliation(id="A00331"))
    for affiliation in affiliations:
        AuthorAffiliations.create(author=author, affiliation=affiliation)

    doc = Document.create(
        id=12345, 
        bibcode="bibcode",
    )
    for author in (author, ):
        DocumentAuthors.create(document=doc, author=author)

    #q = Document.select().join(DocumentAffiliation).join(Affiliation).where(Affiliation.id == "A00331")
    #for doc in q:
    #    print(doc)

    """