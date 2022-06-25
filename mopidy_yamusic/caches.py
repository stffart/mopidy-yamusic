from os.path import exists
from os import mkdir, getenv
import pathlib
from .classes import YMTrack, YMPlaylist
import time
import logging
logger = logging.getLogger("yandex")
import asyncio
import json

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

    def update_like(self, track):
      current_time = int(time.time())
      for p in self._cache:
        #check time
        if current_time - self._playlists_tm[p] > 7200:
           continue
        logger.error(self._cache[p])
        tracks = []
        found = False
        for i, t in enumerate(self._cache[p].tracks):
          if t.uri == track.uri:
             found = True
             if len(tracks) == 0:
               tracks = list(self._cache[p].tracks)
             tracks[i] = track
        if found:
          self.put(YMPlaylist(uri=self._cache[p].uri, name=self._cache[p].name, tracks=tracks))

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
    def __init__(self):
        self._cache = []

    def loadLikes(self, client):
         self._client = client
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


class YMTrackDataCache:
    def __init__(self):
        self._config_dir = pathlib.Path(
            getenv("XDG_CONFIG_HOME", "~/.yatracks")
        ).expanduser()
        logger.error(self._config_dir)
        if not exists(f"{self._config_dir}"):
          mkdir(f"{self._config_dir}")
        self._cache = []

    def put(self, track_id, data, headers):
        if not track_id in self._cache:
          self._cache.append(track_id)
          with open(f"{self._config_dir}/{track_id}","wb") as f:
            f.write(data)
          with open(f"{self._config_dir}/{track_id}.json","w") as f:
            json.dump(headers,f)

    def get(self, track_id):
        data = None
        if exists(f"{self._config_dir}/{track_id}"):
          with open(f"{self._config_dir}/{track_id}","rb") as f:
             data = f.read()

        headers = None
        if exists(f"{self._config_dir}/{track_id}.json"):
          with open(f"{self._config_dir}/{track_id}.json","r") as f:
             headers = json.load(f)

        return (data,headers)
