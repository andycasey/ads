from peewee import SqliteDatabase, Model

database = SqliteDatabase("models.db")

class LocalModel(Model):
    class Meta:
        database = database