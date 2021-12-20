import os
from peewee import SqliteDatabase, Model

database_path = os.path.expanduser("~/.ads/database.db")
database = SqliteDatabase(database_path)

class LocalModel(Model):
    class Meta:
        database = database