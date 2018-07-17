from mopidy.models import Artist, Album, Track


def _get_artist(obj):
    return  Artist(
        uri=obj.uri,
        name=obj.name,
        sortname=obj.sortname,
        musicbrainz_id=obj.musicbrainz_id
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
        'last_modified': t.last_modified
    }
    album_artists = []
    if t.album.artists:
        album_artists.append(_get_artist(t.album.artists))

    data['album'] = Album(
        uri=t.album.uri,
        name=t.album.name,
        artists=album_artists
    )

    if t.artists:
        data['artists'] = [_get_artist(t.artists)]
    if t.composers:
        data['composers'] = [_get_artist(t.composers)]
    if t.performers:
        data['performers'] = [_get_artist(t.performers)]


    return Track(**data)


