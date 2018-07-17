import logging
import itertools
from hashlib import md5

from .models import (db_proxy, Artist, Album, Track, ArtistFTS,
                     AlbumFTS, TrackFTS)


from .utils import to_track

logger = logging.getLogger(__name__)


class Database():
    def __init__(self, db):
        self.db = db
        self.connect(self.db)


    def connect(self, db):
        db_proxy.initialize(db)
        db_proxy.create_tables([
            Artist, 
            Album, 
            Track,
            ArtistFTS,
            AlbumFTS,
            TrackFTS
        ])

    # @db_proxy.on_update
    # def on_update(query_type, db, table, rowid):
    #     logger.info('%s row %s into table %s', query_type, rowid, table)


    def _calc_uri(self, model, data):
        return 'local:{}:md5:{}'.format(
            model,
            md5(str(data)).hexdigest()
        )

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
        if not artist.uri:
            artist = artist.copy(uri=self._calc_uri('artist', artist))

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

        if not album.uri:
            album = album.copy(uri=self._calc_uri('album', album))
        
        db_album, created = Album.get_or_create(
            uri=album.uri,
            defaults=dict(
                name=album.name,
                artists=artists,
                num_tracks=album.num_tracks,
                num_discs=album.num_discs,
                date=album.date,
                musicbrainz_id=album.musicbrainz_id,
                images=album.images
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

        if not track.uri:
            track = track.copy(uri=self._calc_uri('track', track))

        with self.db.atomic():
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


    def tracks(self):
        return itertools.imap(to_track, Track.select())

    def tracks_count(self):
        return Track.select().count()