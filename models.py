from peewee import *


db = SqliteDatabase('music_library.sqlite3')


class Artist(Model):
    name = CharField()

    class Meta:
        database = db


class Album(Model):
    title = CharField()
    recording_date = IntegerField(null=True)
    artist = ForeignKeyField(Artist)

    class Meta:
        database = db


class Track(Model):
    title = CharField()
    duration = IntegerField()
    artist = ForeignKeyField(Artist)
    album = ForeignKeyField(Album)
    md5 = CharField()
    file_name = CharField()

    class Meta:
        database = db


db.create_tables([Artist, Album, Track])
