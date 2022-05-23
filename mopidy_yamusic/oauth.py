import uuid
import requests
import asyncio
from threading import Thread
import logging
import time
from yandex_music import Client
import socket
from os.path import expanduser



logger = logging.getLogger(__name__)

class MetaSingleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(MetaSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class OAuthManager(metaclass=MetaSingleton):

    #client_id = '887c0db290e5443c896c5e6e41347a52'
    #client_secret = 'b87caf622cb44c5aafb9179d80bde5e1'
    client_id = '23cabbbdc6cd418abb4b39c32c41195d'
    client_secret = '53bc75238f0c4d08a118e51fe9203300'

    client_futures = []
    _client = None
    _callbacks = []

    def __init__(self):
        self.node_id = uuid.getnode()
        self.device_uuid = uuid.UUID(int=self.node_id)
        self.device_code = None
        self.device_name = socket.gethostname()
        self.registered_time = None
        self.home = expanduser("~")
        try:
          with open(self.home+'/.yatoken',"r") as token_file:
            self._token = token_file.read()
            if len(self._token) == 0:
              self._token = None
        except:
            self._token = None

        self.loop = asyncio.new_event_loop()
        self.loop.set_exception_handler(self.handle_exception)
        asyncio.run_coroutine_threadsafe(self.try_get_token(),self.loop)
        self.background_thread = Thread(target=self.start_background_loop, args=(self.loop,), daemon=True)
        self.background_thread.start()
        logger.debug("sync coroutine started")

    def handle_exception(self, loop, context):
      # context["message"] will always be there; but context["exception"] may not
      logger.error(f"LOOP EXCEPTION")
      logger.error(context)
      msg = context.get("exception", context["message"])
      logger.error(f"Caught exception: {msg}")

    def start_background_loop(self, loop: asyncio.AbstractEventLoop) -> None:
       try:
         asyncio.set_event_loop(loop)
         loop.run_forever()
       except Exception:
         logger.error(sys.exc_info())

    def init_service(self):
      self._likes_cache.loadLikes()

    def add_callback(self, callback):
      self._callbacks.append(callback)

    def register_device(self):
      t = int(time.time())
      if self.registered_time != None:
        if self.registered_time > t:
          logger.error('time is not yet elapsed')
          return self
      params = {
      'client_id': self.client_id,
      'device_id': str(self.device_uuid),
      'device_name': self.device_name
      }
      res = requests.post('https://oauth.yandex.ru/device/code',data=params,json={}).json()
      self.device_code = res['device_code']
      self.verification_url = res['verification_url']
      self.user_code = res['user_code']
      self.registered_time = int(time.time())+300
      return self

    @asyncio.coroutine
    def try_get_token(self):
      token = None
      while True:
         logger.debug('try get token')
         token = self.get_token()
         if token == None:
           yield from asyncio.sleep(5)
         else:
           break
      logger.debug('init client with token '+token)
      self._client = Client(token).init()
      logger.debug('init finished')
      for c in self._callbacks:
        c(self._client)

      for f in self.client_futures:
        logger.debug('set future result')
        f.set_result(self._client)
      logger.debug('token get success')

    def get_token(self):
      if self._token != None:
         return self._token

      if self.device_code == None:
         return None

      params = {
      'client_id': self.client_id,
      'client_secret': self.client_secret,
      'grant_type': 'device_code',
      'code':self.device_code
      }
      res = requests.post('https://oauth.yandex.ru/token',data=params).json()
      if 'access_token' in res:
        self._token = res['access_token']
        with open(self.home+'/.yatoken',"w") as token_file:
           token_file.write(self._token)
      else:
        self._token = None
      return self._token

    def get_client(self):
      client_future = asyncio.Future()
      if self._token != None:
        self._client = Client(self._token).init()
      if self._client != None:
        client_future.set_result(self._client)
      else:
        self.client_futures.append(client_future)
      return client_future


