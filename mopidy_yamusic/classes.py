from mopidy.models import Playlist, Track, Ref, fields, Artist, Album
from yandex_music import Playlist as YPlaylist, Track as YTrack, Artist as YArtist, Album as YAlbum
import logging
logger = logging.getLogger("yandex")

class YMTrack(Track):
    @staticmethod
    def from_track(track: YTrack, like=False):
        uri = f"yandexmusic:track:{track.id}"
        name = track.title
        length = track.duration_ms
        artists = list(map(YMArtist.from_artist, track.artists))
        albums = list(map(YMAlbum.from_album, track.albums))
        if len(albums) > 0:
          album = albums[0]
        else:
          album = YMAlbum(uri="",name="",artists=[],artwork="")
        artwork = track.cover_uri.replace('%%','%1x%2')
        return YMTrack(uri=uri, name=name, length=length, artwork=artwork, artists=artists, album=album, like=like)

    def switchLike(self):
       return YMTrack(uri=self.uri, name=self.name, length=self.length, artwork=self.artwork, artists=self.artists, album=self.album, like=(not self.like))

    artwork = fields.String()
    like = fields.Boolean()


class YMRef(Ref):
    @staticmethod
    def from_raw(owner: str, playlist_id: str, title: str, artwork: str = "", generated: bool = False):
        uri = f"yandexmusic:playlist:{owner}:{playlist_id}"
        name = title
        ref = YMRef(type=Ref.PLAYLIST, uri=uri, name=name, artwork=artwork, generated=generated)

        return ref

    @staticmethod
    def root():
        uri = f"yandexmusic:directory:root"
        name = "Яндекс Музыка"
        artwork = "yastatic.net/doccenter/images/support.yandex.com/en/music/freeze/fzG5B6KxX0dggCpZn4SQBpnF4GA.png"
        description = "Cервис"
        ref = YMRef(type=Ref.PLAYLIST, uri=uri, name=name, artwork=artwork, description=description)

        return ref

    @staticmethod
    def from_directory(id,name,artwork,desc):
        uri = f"yandexmusic:directory:{id}"
        name = name
        ref = YMRef(type=Ref.DIRECTORY, uri=uri, name=name, artwork=artwork, description=desc)
        return ref

    @staticmethod
    def from_playlist(playlist: YPlaylist):
        uri = f"yandexmusic:playlist:{playlist.owner.uid}:{playlist.kind}"
        name = playlist.title
        artwork = ''
        if playlist.cover.uri != None:
          artwork = playlist.cover.uri.replace('%%','%1x%2')
        else:
          if playlist.cover.items_uri != None:
            artwork = playlist.cover.items_uri[0].replace('%%','%1x%2')
        if hasattr(playlist,"generated"):
          generated = playlist.generated
        else:
          generated = False
        ref = YMRef(type=Ref.PLAYLIST, uri=uri, name=name, artwork=artwork, generated=generated)

        return ref

    @staticmethod
    def from_track(track: YTrack):
        uri = f"yandexmusic:track:{track.id}"
        name = track.title
        artwork = track.cover_uri.replace('%%','%1x%2')
        artists = list(map(YMArtist.from_artist, track.artists))
        albums = list(map(YMAlbum.from_album, track.albums))
        if len(albums) > 0:
          album = albums[0]
        else:
          album = YMAlbum(uri="",name="",artists=[],artwork="")
        ref = YMRef(type=Ref.TRACK, uri=uri, name=name, artwork=artwork, artists=artists, album=album)

        return ref

    @staticmethod
    def from_ytrack(track: YMTrack):
        ref = YMRef(type=Ref.TRACK, uri=track.uri, name=track.name, artwork=track.artwork, artists=track.artists, album=track.album)
        return ref

    @staticmethod
    def from_artist(artist: YArtist):
        uri = f"yandexmusic:artist:{artist.id}"
        name = artist.name
        if artist.cover != None:
          artwork = artist.cover.uri.replace('%%','%1x%2')
        else:
          artwork = ''
        ref = YMRef(type=Ref.ARTIST, uri=uri, name=name, artwork=artwork)

        return ref

    @staticmethod
    def from_album(album: YAlbum):
        uri = f"yandexmusic:album:{album.id}"
        name = f"{album.title} ({album.year})"
        artists = list(map(YMArtist.from_artist, album.artists))
        artwork = album.cover_uri.replace('%%','%1x%2')
        ref = YMRef(type=Ref.ARTIST, uri=uri, name=name, artwork=artwork, artists=artists)

        return ref

    artwork = fields.String()
    #: The artists matching the search query. Read-only.
    artists = fields.Collection(type=Artist, container=tuple)

    #: The albums matching the search query. Read-only.
    album = fields.Field(type=Album)
    description = fields.String()
    generated = fields.Boolean()

class YMPlaylist(Playlist):
    @staticmethod
    def from_playlist(playlist: YPlaylist):
        uri = f"yandexmusic:playlist:{playlist.owner.uid}:{playlist.kind}"
        name = playlist.title
        tracks = []
        for track in playlist.tracks:
          ytrack = YMTrack.from_track(track,track.liked)
          tracks.append(ytrack)
        #tracks = list(map(YMTrack.from_track, playlist.tracks))
        if hasattr(playlist,"generated"):
          generated = playlist.generated
        else:
          generated = False
        return YMPlaylist(uri=uri, name=name, tracks=tracks, revision=playlist.revision, generated=generated)

    revision = fields.Integer()
    generated = fields.Boolean()


class YMArtist(Artist):
    @staticmethod
    def from_artist(artist: YArtist):
        uri = f"yandexmusic:artist:{artist.id}"
        name = artist.name
        if artist.cover != None:
          artwork = artist.cover.uri.replace('%%','%1x%2')
        else:
          artwork = ''
        return YMArtist(uri=uri, name=name, artwork=artwork)

    artwork = fields.String()

class YMAlbum(Album):
    @staticmethod
    def from_album(album: YAlbum):
        uri = f"yandexmusic:album:{album.id}"
        name = f"{album.title} ({album.year})"
        artists = list(map(YMArtist.from_artist, album.artists))
        artwork = album.cover_uri.replace('%%','%1x%2')
        yalbum = YMAlbum(uri=uri, name=name, artists=artists, artwork=artwork)
        return yalbum

    artwork = fields.String()
