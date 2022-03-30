from .classes import YMTrack

import logging
logger = logging.getLogger("yandex")

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

