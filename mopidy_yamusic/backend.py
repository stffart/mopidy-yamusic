from mopidy import backend, audio
import pykka
import yandex_music
from .playlist_provider import YandexMusicPlaylistProvider
from .playback_provider import YandexMusicPlaybackProvider
from .library_provider import YandexMusicLibraryProvider
from .caches import YMTrackCache, YMLikesCache, YMPlaylistCache
from .oauth import OAuthManager
import asyncio

import logging
logger = logging.getLogger("yandex")

class YaMusicBackend(pykka.ThreadingActor, backend.Backend):
    def __init__(self, config: dict, audio: audio):
        super(YaMusicBackend, self).__init__()

        ym_config :dict = config["yamusic"]

        bitrate = int(ym_config["bitrate"]) if "bitrate" in ym_config else 192

        self._config = config
        self._audio = audio
        oauth = OAuthManager()
        track_cache = YMTrackCache()
        likes_cache = YMLikesCache()
        oauth.add_callback(likes_cache.loadLikes)
        playlist_cache = YMPlaylistCache()
        url = "http://"+config["http"]["hostname"]+":"+str(config["http"]["port"])+"/yamusic/track/"

        self.playlists = YandexMusicPlaylistProvider(self, track_cache, likes_cache, playlist_cache)
        oauth.add_callback(self.playlists.setClient)
        self.playback = YandexMusicPlaybackProvider(audio, self, bitrate, url)
        oauth.add_callback(self.playback.setClient)
        self.library = YandexMusicLibraryProvider(track_cache, likes_cache, playlist_cache)
        oauth.add_callback(self.library.setClient)

        self.uri_schemes = ["yandexmusic"]
