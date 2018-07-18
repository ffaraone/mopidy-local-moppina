import logging
import itertools
from hashlib import md5

from .models import (db_proxy, Artist, Album, Track, ArtistFTS,
                     AlbumFTS, TrackFTS)

from peewee import fn, SQL


logger = logging.getLogger(__name__)


class Database():
    def __init__(self, db):
        self._db = db
        self.connect()


    def connect(self):
        db_proxy.initialize(self._db)
        db_proxy.create_tables([
            Artist, 
            Album, 
            Track,
            ArtistFTS,
            AlbumFTS,
            TrackFTS
        ])

    def close(self):
        self._db.execute_sql('ANALYZE')
        self._db.close()

    def clear(self):
        logger.info('local-moppina: clear database')
        with self._db.atomic():
            self._db.execute_sql('DELETE FROM trackfts')
            self._db.execute_sql('DELETE FROM track')
            self._db.execute_sql('DELETE FROM albumfts')
            self._db.execute_sql('DELETE FROM album')
            self._db.execute_sql('DELETE FROM artistfts')
            self._db.execute_sql('DELETE FROM artist')
        self._db.execute_sql('VACUUM')

        

    def _upsert_artists_fts(self, artist):
        fts_artist, created = ArtistFTS.get_or_create(
            rowid=artist.id,
            defaults=dict(
                uri=artist.uri,
                name=artist.name
            )
        )
        if not created:
            fts_artist.uri = artist.uri
            fts_artist.name = artist.name
            fts_artist.save()


    def _upsert_artists(self, artists):
        if not artists:
            return
        artist = next(iter(artists))

        db_artist, created = Artist.get_or_create(
            uri=artist.uri,
            defaults=dict(
                name=artist.name,
                sortname=artist.sortname,
                musicbrainz_id=artist.musicbrainz_id
            )
        )
        if not created:
            db_artist.name = artist.name
            db_artist.sortname = artist.sortname
            db_artist.musicbrainz_id = artist.musicbrainz_id
            db_artist.save()

        self._upsert_artists_fts(db_artist)
        
        return db_artist


    def _upsert_album_fts(self, album):
        fts_album, created = AlbumFTS.get_or_create(
            rowid=album.id,
            defaults=dict(
                uri=album.uri,
                name=album.name,
                artist=album.artists.name
            )
        )
        if not created:
            fts_album.uri = album.uri
            fts_album.name = album.name
            fts_album.artist = album.artists.name
            fts_album.save()

    def _upsert_album(self, album):
        artists = self._upsert_artists(album.artists)
        logger.debug('local-moppina upsert album, artist: %s', artists)
        
        db_album, created = Album.get_or_create(
            uri=album.uri,
            defaults=dict(
                name=album.name,
                artists=artists,
                num_tracks=album.num_tracks,
                num_discs=album.num_discs,
                date=album.date,
                musicbrainz_id=album.musicbrainz_id,
                images=' '.join(album.images) if album.images else None
            )
        )

        if not created:
            db_album.name = album.name
            db_album.artists = artists
            db_album.num_tracks = album.num_tracks
            db_album.num_discs = album.num_discs
            db_album.date = db_album.date
            db_album.musicbrainz_id = album.musicbrainz_id
            db_album.images = album.images
            db_album.save()
        
        self._upsert_album_fts(db_album)

        return db_album


    def _upsert_track_fts(self, track):
        fts_track, created = TrackFTS.get_or_create(
            rowid=track.id,
            defaults=dict(
                uri=track.uri,
                track_name=track.name,
                album=track.album.name,
                artist=track.artists.name if track.artists else None,
                composer=track.composers.name if track.composers else None,
                performer=track.performers.name if track.performers else None,
                albumartist=track.album.artists.name if track.album.artists else None,
                genre=track.genre,
                track_no=track.track_no,
                date=track.date,
                comment=track.comment
            )
        )
        if not created:
            fts_track.uri = track.uri
            fts_track.track_name = track.name
            fts_track.album = track.album.name
            fts_track.artist = track.artists.name if track.artists else None
            fts_track.composer = track.composers.name if track.composers else None
            fts_track.performer = track.performers.name if track.performers else None
            fts_track.albumartist = track.album.artists.name if track.album.artists else None
            fts_track.genre = track.genre
            fts_track.track_no = track.track_no
            fts_track.date = track.date
            fts_track.comment = track.comment
            fts_track.save()       


    def upsert_track(self, track):
        logger.debug('local-moppina: process track %s', track)

        with self._db.atomic():
            album = None
            artists = None
            composers = None
            performers = None
            if track.album:
                album = self._upsert_album(track.album)
            if track.artists:
                artists = self._upsert_artists(track.artists)
            if track.composers:
                composers = self._upsert_artists(track.composers)
            if track.performers:
                performers = self._upsert_artists(track.performers)

            db_track, created = Track.get_or_create(
                uri=track.uri,
                defaults=dict(
                    name=track.name,
                    album=album,
                    artists=artists,
                    composers=composers,
                    performers=performers,
                    genre=track.genre,
                    track_no=track.track_no,
                    disc_no=track.disc_no,
                    date=track.date,
                    length=track.length,
                    bitrate=track.bitrate,
                    comment=track.comment,
                    musicbrainz_id=track.musicbrainz_id,
                    last_modified=track.last_modified
                )
            )
            if not created:
                    db_track.name = track.name
                    db_track.album = album
                    db_track.artists = artists
                    db_track.composers = composers
                    db_track.performers = performers
                    db_track.genre = track.genre
                    db_track.track_no = track.track_no
                    db_track.disc_no = track.disc_no
                    db_track.date = track.date
                    db_track.length = track.length
                    db_track.bitrate = track.bitrate
                    db_track.comment = track.comment
                    db_track.musicbrainz_id = track.musicbrainz_id
                    db_track.last_modified = track.last_modified
        
            self._upsert_track_fts(db_track)


    def artists(self):
        return Artist.select().order_by(Artist.name)

    def albums(self):
        return Album.select().order_by(Album.artists, Album.name)

    def tracks(self):
        return Track.select()

    def tracks_count(self):
        return Track.select().count()


    def albums_by_artist(self, uri):
        logger.debug('local-moppina: get albums for artist %s', uri)
        return (Album.select()
            .join(Artist)
            .where(Artist.uri == uri)
            .order_by(Album.name))


    def tracks_by_album(self, uri):
        return (Track.select()
            .join(Album)
            .where(Album.uri == uri)
            .order_by(Track.track_no))

    def tracks_by_artist(self, uri):
        return (Track.select()
            .join(Album)
            .join(Artist)
            .where(Artist.uri == uri))
    
    def track_by_uri(self, uri):
        return (Track.select()
            .where(Track.uri == uri))

    def delete_track(self, uri):
        Track.delete().where(Track.uri == uri)

    def get_distinct(self, field, query):
        model_field = getattr(TrackFTS, field, None)
        if not model_field:
            return set()

        q = SQL('1 = 1')

        for f, values in query.iteritems():
            for value in values:
                q &= getattr(TrackFTS, f) == value

        
        qs = TrackFTS.select(fn.Distinct(model_field)).where(q)
        results = qs.scalar(as_tuple=True)
        return set(results) if results else set()

    def _search(self, model, query, limit, offset):
        q = SQL('1 = 1')
        for field, values in query.iteritems():
            if field == 'any':
                or_cond = SQL('1 = 0')
                for field_name in model._meta.fields.keys():
                    if field_name == 'id':
                        continue
                        for value in values:
                            or_cond |= getattr(model, field_name) == value
                q &= or_cond
                continue
                
            if hasattr(model, field):
                for value in values:
                    q &= getattr(model, field) == value
        
        return model.select().where(q).limit(limit).offset(offset)        


    def _fts_search(self, model, ftsmodel, query, limit, offset):
        q = ftsmodel.match('')
        for field_values in query.values():
            for val in field_values:
                q |= ftsmodel.match(val)


        ids = (ftsmodel.select(ftsmodel.rowid).where(q)
            .order_by(ftsmodel.bm25())
            .limit(limit)
            .offset(offset)
            .scalar(as_tuple=True))

        return model.select().where(model.id << ids)

    # def _fts_artist_search(self, query, limit, offset):
    #     q = ArtistFTS.match('')
    #     for field_values in query.values():
    #         for val in field_values:
    #             q |= ArtistFTS.match(val)


    #     # ids = (ArtistFTS.select(ArtistFTS.rowid).where(q)
    #     #     .order_by(ArtistFTS.bm25())
    #     #     .limit(limit)
    #     #     .offset(offset)
    #     #     .scalar(as_tuple=True))

    #     return Artist.select().where(Artist.id << ids)

    def search(self, query, limit, offset):
        return (self._search(Artist, query, limit, offset),
            self._search(Album, query, limit, offset),
            self._search(Track, query, limit, offset))

    def fts_search(self, query, limit, offset):
        return (
            self._fts_search(Artist, ArtistFTS, query, limit, offset),
            self._fts_search(Album, AlbumFTS, query, limit, offset),
            self._fts_search(Track, TrackFTS, query, limit, offset),
        )