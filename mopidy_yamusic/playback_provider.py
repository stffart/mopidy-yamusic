from mopidy import backend, audio
from yandex_music import Client
import logging
logger = logging.getLogger("yandex")


class YandexMusicPlaybackProvider(backend.PlaybackProvider):
    def __init__(self, audio: audio.Audio, backend: backend.Backend, bitrate:int, url:str):
        super().__init__(audio, backend)
        self._bitrate = bitrate
        self._url = url

    def setClient(self, client):
        self._client = client

    def translate_uri(self, uri: str):
        logger.debug('translate')
        logger.debug(uri)
        params = uri.split(":")
        kind = params[1]
        if kind == 'track':
          return self._url+uri
          track_id = params[2]
          uid = f"{track_id}"
          infos = self._client.tracks_download_info(uid, get_direct_links=True)
          for info in infos:
              if info.codec == "mp3" and info.bitrate_in_kbps == self._bitrate:
                  link = info.direct_link
                  return link
        return None
