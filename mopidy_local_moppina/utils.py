import os
import sys
from hashlib import md5
from mopidy.models import Artist, Album, Track
from mopidy.local import translator

def to_artist(a):
    return  Artist(
        uri=a.uri,
        name=a.name,
        sortname=a.sortname,
        musicbrainz_id=a.musicbrainz_id
    )

def to_album(a):
    return Album(
        uri=a.uri,
        name=a.name,
        artists=[to_artist(a.artists)] if a.artists else []
    )    

def to_track(t):
    data = {
        'uri': t.uri,
        'name': t.name,
        'genre': t.genre,
        'track_no': t.track_no,
        'disc_no': t.disc_no,
        'date': t.date,
        'length': t.length,
        'bitrate': t.bitrate,
        'comment': t.comment,
        'musicbrainz_id': t.musicbrainz_id,
        'last_modified': t.last_modified,
        'album': to_album(t.album)
    }

    if t.artists:
        data['artists'] = [to_artist(t.artists)]
    if t.composers:
        data['composers'] = [to_artist(t.composers)]
    if t.performers:
        data['performers'] = [to_artist(t.performers)]


    return Track(**data)


def calc_uri(model, data):
    return 'local:{}:md5:{}'.format(
        model,
        md5(str(data)).hexdigest()
    )

def check_artist(artist):
    if not artist.name:
        raise ValueError('No artist name')
    return artist.copy(uri=artist.uri or calc_uri('artist', artist))

def check_track(track):
    if not track.uri:
        raise ValueError('Track without URI')

    name = ''
    if track.name:
        name = track.name
    else:
        path = translator.local_track_uri_to_path(track.uri, '')
        name = os.path.basename(path).decode(sys.getfilesystemencoding(), 
                                             errors='replace')

    album = None
    if track.album and track.album.name:
        albumartist = None
        if track.album.artists:
            albumartist = map(check_artist, track.album.artists)
        else:
            albumartist = map(check_artist, track.artists)
        album = track.album.copy(
            uri=track.album.uri or calc_uri('album', track.album),
            artists=albumartist
        )
    else:
        raise ValueError('track without album')
    return track.copy(
        name=name,
        album=album,
        artists=map(check_artist, track.artists),
        composers=map(check_artist, track.composers),
        performers=map(check_artist, track.performers)
    )