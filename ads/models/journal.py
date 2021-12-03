"""
Journal data model.
"""
from ads.models.local import LocalModel

from peewee import TextField


class Journal(LocalModel):

    """ A journal produced by a publisher. """

    abbreviation = TextField(primary_key=True) 
    full_name = TextField()


if __name__ == "__main__":

    from ads.models.local import database

    database.connect()
    database.create_tables([Journal], safe=True)
    database.close()


    import json
    with open("journals.json", "r") as fp:
        journals = json.load(fp)
    
    for abbreviation, full_name in journals.items():
        with database.atomic():
            Journal.create(abbreviation=abbreviation, full_name=full_name)
    