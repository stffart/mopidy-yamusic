import logging
import os
import pathlib
import pykka
from mopidy import core
from tornado import gen, web, websocket, httpclient, httputil
logger = logging.getLogger(__name__)
import json
import asyncio
import yandex_music
from .oauth import OAuthManager
from .caches import YMTrackDataCache

class AuthHandler(web.RequestHandler):

    def initialize(self):
      pass

    def get(self, path):
        auth = OAuthManager()
        token = auth.get_token()
        if token == None:
          auth.register_device()
          self.write(f"<body style=\"font-family: Roboto; font-size: 2em; color: #fbfbfb; background-color: #121212; \"><div style=\"position:absolute; top: 40%; left: 30%;\" >To authorize<br />Enter code <p><strong style=\"padding: 5px; background: #242424\" >{auth.user_code}</strong></p> at <a href={auth.verification_url} >{auth.verification_url}</a></div></body>")
        else:
          self.write("<body style=\"font-family: Roboto; font-size: 2em; color: #fbfbfb; background-color: #121212; \"><div style=\"position:absolute; top: 40%; left: 30%;\" >Application authorized.</div></body>")
        self.set_status(200)

class IndexHandler(web.RequestHandler):


    def initialize(self, core, client, client_future, bitrate):
        self._core = core
        self._bitrate = bitrate
        self._client = client
        self._client_future = client_future
        self._response = None
        self._response_headers = []
        self._cache = YMTrackDataCache()

    @gen.coroutine
    def get(self, path):
        uri = path
        range = self.request.headers.get("Range")
        logger.debug(uri)
        params = uri.split(":")
        kind = params[1]
        if kind == 'track':
          track_id = params[2]
          cachedTrack,cachedHeaders = self._cache.get(track_id)
          range_start = None
          range_end = None
          if range != None:
            self.set_status(206)
            if range.split('=')[0] == 'bytes':
              startend = range.split('=')[1].split('-')
              range_start = startend[0]
              range_end = startend[1]
              if range_start != "":
                range_start = int(range_start)
              else:
                range_start = None
              if range_end != "":
                range_end = int(range_end)
              else:
                range_end = None

          if cachedTrack != None:
              logger.error('FROM CACHE')
              if cachedHeaders != None:
                for header in cachedHeaders:
                  if header['name'] == 'Content-Length' and range != None:
                     length = int(header['value'])
                     logger.debug(f"Range start: {range_start}")
                     logger.debug(f"Range end: {range_end}")
                     if range_start != None:
                       length = length - range_start
                       if range_end != None:
                         length = range_end - range_start
                     logger.debug(f"Result length: {length}")
                     self.set_header(header['name'],str(length))
                     continue
                  self.set_header(header['name'],header['value'])
              self.write(cachedTrack[range_start:range_end])
              self.flush()
              self.finish()
              return

          logger.error('FROM YANDEX')

          uid = f"{track_id}"
          logger.debug(uid)
          get_info = False
          while not get_info:
            try:
              if self._client == None:
                if isinstance(self._client_future,asyncio.Future):
                   self._client = self._client_future.result()
              infos = self._client.tracks_download_info(uid, get_direct_links=True)
              get_info = True
            except:
              logger.error("Cannot get track link. Retry...")
              yield asyncio.sleep(5)

          max_bitrate = 0
          max_bitrate_link = None
          link = None
          for info in infos:
              if info.codec == "mp3" and info.bitrate_in_kbps > max_bitrate:
                 max_bitrate = info.bitrate_in_kbps
                 max_bitrate_link = info.direct_link
              if info.codec == "mp3" and info.bitrate_in_kbps == self._bitrate:
                 link = info.direct_link
          if link == None:
             link = max_bitrate_link
          if link != None:
                    logger.debug(link)
                    client = httpclient.AsyncHTTPClient(defaults=dict(request_timeout=900))
                    headers = httputil.HTTPHeaders()
                    if range != None:
                      headers = httputil.HTTPHeaders({"Range":range})
                    requests = [
                       httpclient.HTTPRequest(url=link,headers=headers,streaming_callback=self.on_chunk,header_callback=self.on_headers)
                    ]
                    try:
                      yield list(map(client.fetch,requests))
                    except:
                      #retry
                      yield list(map(client.fetch,requests))
                    self.finish()
                    if range == None:
                      self._cache.put(track_id,self._response,self._response_headers)
                      logger.error("Cached")
                    return
        self.write('Not found')

    def on_headers(self,header):
         params=header.split(': ')
         if len(params) == 2:
           logger.debug(header)
           self._response_headers.append({"name":params[0],"value":params[1].replace('\r\n','')})
           self.set_header(params[0],params[1].replace('\r\n',''))
         if 'HTTP/1.1 206' in header:
           self.set_status(206)

    def on_chunk(self, chunk):
        if self._response == None:
           self._response = chunk
        else:
           self._response = self._response + chunk
        self.write(chunk)
        self.flush()
