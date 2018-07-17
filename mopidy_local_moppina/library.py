from __future__ import unicode_literals

import hashlib
import logging
import operator
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
        self._directories = []
        # for line in ext_config['directories']:
        #     name, uri = line.rsplit(None, 1)
        #     ref = Ref.directory(uri=uri, name=name)
        #     self._directories.append(ref)
        self._dbpath = os.path.join(self._data_dir, 'moppina.db')
        self._connection = SqliteExtDatabase(self._dbpath, pragmas={
            'journal_mode': 'wal',
            'cache_size': -1 * 64000,  # 64MB
            'foreign_keys': 1,
            'ignore_check_constraints': 0
        })
        self._database = db.Database(self._connection)


    def add(self, track, tags=None, duration=None):
        self._database.upsert_track(track)
    
    def begin(self):
        return self._database.tracks()

    def browse(self, uri):
        pass
    
    def clear(self):
        pass
    
    def close(self):
        pass

    def flush(self):
        pass

    def get_distinct(self, field, query=None):
        pass

    def get_images(uris):
        pass

    def load(self):
        return self._database.tracks_count()

    def lookup(self, uri):
        pass

    def remove(self, uri):
        pass
    
    def search(self, query, limit=100, offset=0, exact=False, uris=None):
        pass
    