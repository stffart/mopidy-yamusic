from mopidy import backend
import yandex_music
from .classes import YMRef, YMPlaylist, YMTrack
from typing import List
from .caches import YMTrackCache, YMLikesCache
import logging
import time
import json
import random
logger = logging.getLogger("yandex")
_YM_GENERATED = "yandex-generated"
_YM_LIKED = "yandex-liked"


class YandexMusicPlaylistProvider(backend.PlaylistsProvider):
    _playlists = {}
    _playlists_list = {}
    _playlists_tm = {}

    def __init__(self, backend, client: yandex_music.Client, track_cache: YMTrackCache, likes_cache: YMLikesCache):
        super().__init__(backend)
        self._client = client
        self._track_cache = track_cache
        self._likes_cache = likes_cache
        logger.debug("yandex started")

    def as_list(self) -> List[YMRef]:
        logger.debug("playlist as list")
        if self._playlists_list != {}:
          return self._playlists_list
        yandex_daily = YMRef.from_raw(_YM_GENERATED, "yamusic-daily", "Микс дня", "//avatars.yandex.net/get-music-user-playlist/70586/r5l8ziDPSKyp02/%%")
        yandex_podcasts = YMRef.from_raw(_YM_GENERATED, "yamusic-podcasts", "Подкасты","//avatars.yandex.net/get-music-user-playlist/28719/r5loh7rM0HS0tl/%%")
        yandex_alice = YMRef.from_raw(_YM_GENERATED, "yamusic-origin", "Лист Алисы","//avatars.yandex.net/get-music-user-playlist/71140/r5lnmqmqOdwjQ0/%%")
        yandex_premier = YMRef.from_raw(_YM_GENERATED, "yamusic-premiere", "Премьера","//avatars.yandex.net/get-music-user-playlist/27701/r5ldfjP1rJoson/%%")
        yandex_liked = YMRef.from_raw(_YM_LIKED, "yamusic-liked", "Мне нравится","//music.yandex.ru/blocks/playlist-cover/playlist-cover_like.png")
        playlists = self._client.users_playlists_list()
        refs = []
        refs.extend([yandex_daily, yandex_alice, yandex_premier, yandex_liked, yandex_podcasts])
        user_refs = list(map(YMRef.from_playlist, playlists))
        refs.extend(user_refs)
        self._playlists_list = refs
        logger.debug(refs)
        return refs

    def get_items(self, uri: str) -> YMRef:
        logger.debug("playlist get items")
        _, kind, ym_userid, playlist_id = uri.split(":")
        logger.debug(ym_userid)
        if ym_userid == str(self._client.me.account.uid):
            playlist = self._client.users_playlists(playlist_id)[0]
            track_ids = list(map(lambda t: t.track_id, playlist.tracks))
            tracks = self._client.tracks(track_ids)
            refs = list(map(YMRef.from_track, tracks))
            return refs

    def lookup(self, uri: str) -> YMPlaylist:
            logger.debug("playlist lookup")
            logger.debug(uri)
            _, kind, ym_userid, playlist_id = uri.split(":")
            if playlist_id in self._playlists:
              current = int(time.time())
              if current - self._playlists_tm[playlist_id] < 7200: #caching for 2 hours
                return self._playlists[playlist_id]

            if ym_userid == str(self._client.me.account.uid):
                #User's playlists
                ymplaylist = self._client.users_playlists(playlist_id)
                track_ids = list(map(lambda t: t.track_id, ymplaylist.tracks))
                ymplaylist.tracks = self._client.tracks(track_ids)
                for track in ymplaylist.tracks:
                    track.liked = self._likes_cache.hasLike(track.id)

                playlist = YMPlaylist.from_playlist(ymplaylist)
                for track in playlist.tracks:
                    self._track_cache.put(track)
                self._playlists_tm[playlist_id] = int(time.time())
                self._playlists[playlist_id] = playlist
                return playlist
            elif ym_userid == _YM_LIKED:
                #Random playlist from liked tracks
                tracks = self._client.users_likes_tracks(self._client.me.account.uid)
                ymtracks_id = []
                ymtracks = []
                max_len = 30
                n = 0
                for track in tracks.tracks:
                  ymtracks_id.append(track.id)

                random.shuffle(ymtracks_id)
                ymtracks_id_part = []
                for track in ymtracks_id:
                  ymtracks_id_part.append(track)
                  n = n + 1
                  if n > max_len:
                     break

                ytracks = self._client.tracks(ymtracks_id_part)
                for track in ytracks:
                  ymtracks.append(YMTrack.from_track(track,True))
                uri = f"yandexmusic:playlist:liked"
                name = "Liked"
                playlist = YMPlaylist(uri=uri, name=name, tracks=ymtracks)
                return playlist
            elif ym_userid == _YM_GENERATED:
                #Yandex generated playlist
                foreign_playlist = self._client.feed()['generated_playlists']
                for p in foreign_playlist:
                  logger.debug(p['data']['owner']['name'])
                  if p['data']['owner']['name'] == playlist_id:
                     ymplaylist = p['data']
                track_ids = list(map(lambda t: t.track_id, ymplaylist['tracks']))
                logger.debug(track_ids)
                ymplaylist.tracks = self._client.tracks(track_ids)
                for track in ymplaylist.tracks:
                    track.liked = self._likes_cache.hasLike(track.id)

                playlist = YMPlaylist.from_playlist(ymplaylist)
                for track in playlist.tracks:
                    self._track_cache.put(track)
                self._playlists_tm[playlist_id] = int(time.time())
                self._playlists[playlist_id] = playlist
                return playlist
            else:
                ymplaylist = self._client.users_playlists(playlist_id, user_id=ym_userid)[0]
                track_ids = list(map(lambda t: t.track_id, ymplaylist.tracks))
                ymplaylist.tracks = self._client.tracks(track_ids)
                playlist = YMPlaylist.from_playlist(ymplaylist)
                for track in playlist.tracks:
                    self._track_cache.put(track)
                self._playlists_tm[playlist_id] = int(time.time())
                self._playlists[playlist_id] = playlist
                return playlist


    def create(self, name):
        logger.debug("save")
        logger.debug(name)
        if 'liked:' in name:
          params = name.split(':')
          liked = params[1]
          track_id = params[4]
          uri = f"yandexmusic:track:{track_id}"
          track = self._client.tracks(track_id)[0]
          if liked == 'true':
            self._client.users_likes_tracks_add(track_id)
            self._likes_cache.put(track_id)
            ytrack = YMTrack.from_track(track,True)
            self._track_cache.put(ytrack)
          else:
            self._client.users_likes_tracks_remove(track_id)
            self._likes_cache.remove(track_id)
            ytrack = YMTrack.from_track(track,False)
            self._track_cache.put(ytrack)
        return None

    def delete(self, uri):
        return None

    def refresh(self):
        logger.debug("refresh")
        pass

    def save(self, playlist):
        logger.debug("save")
        logger.debug(playlist)
        return None
