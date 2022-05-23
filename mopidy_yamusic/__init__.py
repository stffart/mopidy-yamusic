from mopidy import ext, config
import pathlib
from .backend import YaMusicBackend
import yandex_music
__version__ = '0.8'
import logging
logger = logging.getLogger("yandex")
from .oauth import OAuthManager

class Extension(ext.Extension):
    dist_name = "Mopidy-YaMusic"
    ext_name = "yamusic"
    version = __version__
    _client = None

    def get_default_config(self):
        default_config = config.read(pathlib.Path(__file__).parent / "ext.conf")
        return default_config

    def get_config_schema(self):
        schema = super().get_config_schema()
        schema["login"] = config.Deprecated()
        schema["password"] = config.Deprecated()
        schema["bitrate"] = config.Integer(optional=True)
        return schema

    def validate_config(self, config):
        return True

    def setup(self, registry):
        registry.add("backend", YaMusicBackend)
        registry.add("http:app", {"name": self.ext_name, "factory": self.webapp})

    def webapp(self, config, core):
        from .web import IndexHandler, AuthHandler
        oauth = OAuthManager()
        oauth.register_device()
        token = oauth.get_token()
        self._client = None
        self._client_future = oauth.get_client()
        return [
            (r"/track/(.+)", IndexHandler, {"core": core, "client": self._client, "client_future":self._client_future, "bitrate": config['yamusic']['bitrate'] }),
            (r"/(.*)", AuthHandler, { }),
        ]
