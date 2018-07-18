from __future__ import unicode_literals
import itertools
import hashlib
import logging

import os
import os.path
import sqlite3
import sys

from mopidy import local
from mopidy.exceptions import ExtensionError
from mopidy.local import translator
from mopidy.models import Ref, SearchResult

import uritools
from playhouse.sqlite_ext import SqliteExtDatabase

from . import Extension
from .utils import to_track, to_album, to_artist, check_track
import db


logger = logging.getLogger(__name__)


class MoppinaLibrary(local.Library):

    name = 'moppina'

    def __init__(self, config):
        self._config = ext_config = config[Extension.ext_name]
        self._data_dir = Extension.get_data_dir(config)
        try:
            self._media_dir = config['local']['media_dir']
        except KeyError:
            raise ExtensionError('Mopidy-Local not enabled')

        self._dbpath = os.path.join(self._data_dir, 'moppina.db')
        self._connection = SqliteExtDatabase(self._dbpath, pragmas={
            'journal_mode': 'wal',
            'cache_size': -1 * 64000,  # 64MB
            'foreign_keys': 1,
            'ignore_check_constraints': 0
        })
        self._db = db.Database(self._connection)
        logger.info('The Moppina library has started successfully')


    def add(self, track, tags=None, duration=None):
        try:
            logger.debug('Try to add the track %s to the Moppina library', 
                         track)
            self._db.upsert_track(check_track(track))
        except Exception as e:
            logger.exception('Failed to add %s to the Moppina library')
    
    def begin(self):
        logger.debug('Begin scan local library with Moppina')
        return itertools.imap(to_track, self._db.tracks())

    def browse(self, uri):
        loggger.info('Browse Moppina library for uri %s', uri)
        try:
            if uri == self.ROOT_DIRECTORY_URI:
                return [
                    Ref.directory(uri='local:artists', name='Artists'),
                    Ref.directory(uri='local:albums', name='Albums'),
                    Ref.directory(uri='local:tracks', name='Tracks')
                ]
            elif uri.startswith('local:artists'):
                return [Ref.artist(uri=a.uri, name=a.name) \
                    for a in self._db.artists()]
            elif uri.startswith('local:albums'):
                return [Ref.album(uri=a.uri, name=a.name) \
                    for a in self._db.albums()]
            elif uri.startswith('local:tracks'):
                return [Ref.track(uri=t.uri, name=t.name) \
                    for t in self._db.tracks()]
            elif uri.startswith('local:artist'):
                return [Ref.album(uri=a.uri, name=a.name) \
                    for a in self._db.albums_by_artist(uri)]
            elif uri.startswith('local:album'):
                return [Ref.track(uri=t.uri, name=t.name) \
                    for t in self._db.tracks_by_album(uri)]
            else:
                raise ValueError('Invalid browse URI')
        except Exception as e:
            logger.error('Error while browsing Moppina library for %s: %s', 
                         uri, e)
            return []
    
    def clear(self):
        logger.info('Clear the Moppina library database')
        self._db.clear()
        return True
    
    def close(self):
        logger.info('Close the Moppina library database')
        self._db.close()

    def flush(self):
        return True

    def get_distinct(self, field, query=None):
        logger.info('Moppina library get distinct for %s: %s', field, query)
        return self._db.get_distinct(field, query or {})

    def load(self):
        logger.debug('Load the Moppina library')
        track_count = self._db.tracks_count()
        logger.info('%s tracks has been loaded by Moppina library')
        return track_count

    def lookup(self, uri):
        logger.info('Lookup Moppina library for %s', uri)
        if uri.startswith('local:album'):
            return itertools.imap(to_track, 
                self._db.tracks_by_album(uri)
            )
        elif uri.startswith('local:artist'):
            return itertools.imap(to_track, 
                self._db.tracks_by_artist(uri)
            )
        elif uri.startswith('local:track'):
            return itertools.imap(to_track, 
                self._db.tracks_by_uri(uri)
            )
        else:
            logger.error('Error looking up the Moppina library: '
                         'invalid lookup URI %s', uri)
            return []

    def remove(self, uri):
        logger.info('Remove %s from the Moppina library')
        self._db.delete_track(uri)
    
    def search(self, query, limit=100, offset=0, exact=False, uris=None):
        logger.info('Search the Moppina library for %s: %s', query, exact)
        if not query:
            tracks = self._db.tracks().limit(limit).offset(offset)
            mopidy_tracks = itertools.imap(to_track, tracks)
            return SearchResult(uri='local:search', tracks=mopidy_tracks)
        artists = []
        albums = []
        tracks = []

        if exact:
            artists, albums, tracks = self._db.search(query, limit, offset)
        else:
            artists, albums, tracks = self._db.fts_search(query, limit, offset)

        mopidy_artists = itertools.imap(to_artist, artists)
        mopidy_albums = itertools.imap(to_album, albums)
        mopidy_tracks = itertools.imap(to_track, tracks)
        return SearchResult(uri='local:search', 
                            artists=mopidy_artists,
                            albums=mopidy_albums,
                            tracks=mopidy_tracks)
