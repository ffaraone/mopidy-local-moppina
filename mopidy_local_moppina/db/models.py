from __future__ import unicode_literals

from peewee import *

db_proxy = Proxy()

class BaseModel(Model):
    class Meta:
        database = db_proxy

class Artist(BaseModel):
    uri = TextField(
        unique=True
    )
    name = TextField(
        index=True
    )
    musicbrainz_id = TextField(
        null=True
    )

class Album(BaseModel):
    uri = TextField(
        unique=True
    )
    name = TextField(
        index=True
    )
    artists = ForeignKeyField(
        Artist, 
        backref='albums', 
        index=True
    )
    num_tracks = IntegerField(
        null=True
    )
    num_discs = IntegerField(
        null=True
    )
    date = TextField(
        null=True
    ) # index ?
    musicbrainz_id = TextField(
        null=True
    )
    images = TextField(
        null=True
    )


class Track(BaseModel):
    uri = TextField(
        unique=True
    )
    name = TextField(
        index=True
    )
    album = ForeignKeyField(
        Album, 
        backref='tracks', 
        index=True
    )
    artists = ForeignKeyField(
        Artist, 
        backref='artist_tracks', 
        index=True
    )
    composers = ForeignKeyField(
        Artist, 
        backref='composer_tracks', 
        index=True
    )
    performers = ForeignKeyField(
        Artist, 
        backref='performer_tracks', 
        index=True
    )
    genre = TextField(
        null=True, 
        index=True
    )
    track_no = IntegerField(
        null=True
    ) # index ?
    disc_no = IntegerField(
        null=True
    )
    date = TextField(
        null=True
    ) # index ?
    length = IntegerField(
        null=True
    )
    bitrate = IntegerField(
        null=True
    )
    comment = TextField(
        null=True
    ) # index ?
    musicbrainz_id = TextField(
        null=True
    )
    last_modified = IntegerField(
        null=True
    )  # index ?

