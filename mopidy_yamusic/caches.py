from .classes import YMTrack, YMPlaylist
import time
import logging
logger = logging.getLogger("yandex")

class YMPlaylistCache:

    _playlists = {}

    def __init__(self):
        self._cache = dict()
        self._playlists_tm = dict()

    def put(self, playlist: YMPlaylist):
        self._cache[playlist.uri] = playlist
        self._playlists_tm[playlist.uri] = int(time.time())

    def get(self, uri: str) -> YMPlaylist:
        if uri not in self._cache:
            return None
        playlist = self._cache[uri]
        return playlist


    def put_list(self, list):
      self._playlists = list

    def get_list(self):
      return self._playlists

    def in_cache(self, uri):
      current_time = int(time.time())
      return (uri in self._cache) and (current_time - self._playlists_tm[uri] < 7200) #caching for 2 hours

class YMTrackCache:
    def __init__(self):
        self._cache = dict()

    def put(self, track: YMTrack):
        self._cache[track.uri] = track

    def get(self, uri: str) -> YMTrack:
        if uri not in self._cache:
            return None

        track = self._cache[uri]
        return track


class YMLikesCache:
    def __init__(self, client):
        self._cache = []
        self._client = client
        self.loadLikes()

    def loadLikes(self):
         self._cache = []
         tracks = self._client.users_likes_tracks(self._client.me.account.uid)
         for track in tracks.tracks:
            self._cache.append(track.id)

    def put(self, track_id):
        if not track_id in self._cache:
          self._cache.append(track_id)

    def remove(self, track_id):
        if track_id in self._cache:
          self._cache.remove(track_id)

    def hasLike(self, track_id):
        return str(track_id) in self._cache

