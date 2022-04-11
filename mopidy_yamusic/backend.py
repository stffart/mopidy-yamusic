from mopidy import backend, audio
import pykka
import yandex_music
from .playlist_provider import YandexMusicPlaylistProvider
from .playback_provider import YandexMusicPlaybackProvider
from .library_provider import YandexMusicLibraryProvider
from .caches import YMTrackCache, YMLikesCache, YMPlaylistCache

class YaMusicBackend(pykka.ThreadingActor, backend.Backend):
    def __init__(self, config: dict, audio: audio):
        super(YaMusicBackend, self).__init__()

        ym_config :dict = config["yamusic"]

        login = ym_config["login"]
        password = ym_config["password"]
        bitrate = int(ym_config["bitrate"]) if "bitrate" in ym_config else 192

        self._config = config
        self._audio = audio

        client = yandex_music.Client.from_credentials(username=login, password=password)
        track_cache = YMTrackCache()
        likes_cache = YMLikesCache(client)
        playlist_cache = YMPlaylistCache()

        self.playlists = YandexMusicPlaylistProvider(self, client, track_cache, likes_cache, playlist_cache)
        self.playback = YandexMusicPlaybackProvider(client, audio, self, bitrate)
        self.library = YandexMusicLibraryProvider(client, track_cache, likes_cache, playlist_cache)

        self.uri_schemes = ["yandexmusic"]
