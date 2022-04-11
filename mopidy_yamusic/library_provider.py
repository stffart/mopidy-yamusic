from mopidy import backend, models, config
from yandex_music import Client
from .caches import YMTrackCache, YMLikesCache, YMPlaylistCache
from .classes import YMTrack, YMArtist, YMAlbum, YMRef, YMPlaylist
import logging
logger = logging.getLogger("yandex")
logging.basicConfig(level=logging.DEBUG)

class YandexMusicLibraryProvider(backend.LibraryProvider):
    def __init__(self, client: Client, track_cache: YMTrackCache, likes_cache: YMLikesCache, playlist_cache: YMPlaylistCache):
        self._client = client
        self._track_cache = track_cache
        self._likes_cache = likes_cache
        self.root_directory = YMRef.root()
        self._playlist_cache = playlist_cache
        self._feed_cache = {"days":[{"events":[]}]}

    def browse(self, uri):
        logger.debug('browse')
        logger.debug(uri)
        refs = []
        feed = self._client.feed()
        self._feed_cache = feed
        params = uri.split(':')
        if uri == 'yandexmusic:directory:root':
          for event in self._feed_cache.days[0].events:
            artwork = ''
            description = ''
            if event.type == 'artists':
               artwork = event.artists[0].artist.cover.uri.replace('%%','%1x%2')
               description = 'Исполнители'
            if event.type == 'tracks':
               artwork = event.tracks[0].cover_uri.replace('%%','%1x%2')
               description = 'Треки'
            if event.type == 'albums':
               artwork = event.albums[0].album.cover_uri.replace('%%','%1x%2')
               description = 'Альбомы'
            refs.append(YMRef.from_directory(event.id,event.title,artwork,description))
        else:
          kind = params[1]
          if kind == 'directory':
            id = params[2]
            thisevent = None
            for event in feed.days[0].events:
              if event.id == id:
                thisevent = event
                break
            tracks = thisevent.tracks
            ymrefs = []
            for artist in thisevent.artists:
               ymrefs.append(YMRef.from_artist(artist['artist']))
            for album in thisevent.albums:
               ymrefs.append(YMRef.from_album(album))
            for track in tracks:
               ymrefs.append(YMRef.from_track(track))
            return ymrefs
          if kind == 'artist':
            ymartist_id = params[2]
            tracks = self._client.artists_tracks(ymartist_id)
            ymrefs = []
            for track in tracks:
              uri = f"yandexmusic:track:{track.id}"
              name = track.title
              length = track.duration_ms
              artists = list(map(YMArtist.from_artist, track.artists))
              artwork = track.cover_uri.replace('%%','%1x%2')
              ymtrack =  YMTrack(uri=uri, name=name, length=length, artwork=artwork, artists=artists)
              self._track_cache.put(ymtrack)
              ymrefs.append(YMRef.from_ytrack(ymtrack))
            return ymrefs
          return res_tracks

        return refs

    def search(self, query, uris = None, exact = False):
        logger.debug('library search')
        logger.debug(query)
        kind = ''
        if 'any' in query:
          ya_query = " ".join(query['any'])
          kind = 'any'
        if 'artist' in query:
          ya_query = " ".join(query['artist'])
          kind = 'artist'
        if 'album' in query:
          ya_query = " ".join(query['album'])
          kind = 'album'
        if 'track' in query:
          ya_query = " ".join(query['track'])
          kind = 'track'
        search_result = self._client.search(ya_query.encode('utf-8'))
        if search_result['best'] == None:
          return None
        res_artists = []
        res_tracks = []
        res_albums = []
        #Best
        logger.debug(search_result['best'].type)
        best_uri = ''
        if search_result['best'].type == 'artist':
          res_artists = [YMArtist.from_artist(search_result['best']['result'])]
          albums = self._client.artists_direct_albums(search_result['best']['result'].id)
          for album in albums:
            res_albums.append(YMAlbum.from_album(album))
          best_uri = res_artists[0].uri

        if search_result['best'].type == 'album':
          res_albums = [YMAlbum.from_album(search_result['best']['result'])]
          best_uri = res_albums[0].uri

        if search_result['best'].type == 'track':
          res_tracks = [YMTrack.from_track(search_result['best']['result'],self._likes_cache.hasLike(search_result['best']['result'].id))]
          best_uri = res_tracks[0].uri

        #Other
        if search_result['albums'] != None:
          max_albums = 1
          index = 1
          for album in search_result['albums']['results']:
            if search_result['best'].type == 'album':
              if search_result['best']['result'].id == album.id:
                 continue
            res_albums.append(YMAlbum.from_album(album))
            index = index + 1
            if index > max_albums:
              break

        if search_result['tracks'] != None:
          max_tracks = 5
          index = 1
          for track in search_result['tracks']['results']:
            if search_result['best'].type == 'track':
              if search_result['best']['result'].id == track.id:
                continue
            res_tracks.append(YMTrack.from_track(track,self._likes_cache.hasLike(track.id)))
            index = index + 1
            if index > max_tracks:
              break

        if search_result['artists'] != None:
          max_artists = 1
          index = 1
          for artist in search_result['artists']['results']:
            if search_result['best'].type == 'artist':
              if search_result['best']['result'].id == artist.id:
                 continue
            res_artists.append(YMArtist.from_artist(artist))
            index = index + 1
            if index > max_artists:
              break


        sresult = models.SearchResult(uri='', tracks=res_tracks, artists=res_artists, albums=res_albums)
        logger.debug(sresult)
        return sresult

    def lookup(self, uri: str):
        logger.debug('lookup')
        logger.debug(uri)
        track = self._track_cache.get(uri)
        if track is not None:
            return [track]

        params = uri.split(":")
        kind = params[1]
        if kind == 'track':
          ymtrack_id = params[2]
          track_id = f"{ymtrack_id}"
          ymtrack = self._client.tracks(track_id)
          track = YMTrack.from_track(ymtrack[0],self._likes_cache.hasLike(track_id))
          logger.debug(track.uri)
          self._track_cache.put(track)
          return [track]
        if kind == 'artist':
          ymartist_id = params[2]
          tracks = self._client.artists_tracks(ymartist_id)
          res_tracks = []
          for track in tracks:
            logger.debug(track)
            uri = f"yandexmusic:track:{track.id}"
            name = track.title
            length = track.duration_ms
            artists = list(map(YMArtist.from_artist, track.artists))
            artwork = track.cover_uri.replace('%%','%1x%2')
            ymtrack =  YMTrack(uri=uri, name=name, length=length, artwork=artwork, artists=artists)
            self._track_cache.put(ymtrack)
            res_tracks.append(ymtrack)
          return res_tracks
        if kind == 'album':
          ymalbum_id = params[2]
          tracks = self._client.albums_with_tracks(ymalbum_id)
          res_tracks = []
          for vol in tracks['volumes']:
            for track in vol:
              ymtrack = YMTrack.from_track(track,self._likes_cache.hasLike(track.id))
              self._track_cache.put(ymtrack)
              res_tracks.append(ymtrack)
          return res_tracks
        return []

    def get_images(self, uris):
        logger.error('get_images')
        logger.error(uris)
        result = dict()

        for uri in uris:
            _, kind, id = uri.split(":", 2)
            if kind == "directory":
              for event in self._feed_cache.days[0].events:
                 artwork = ''
                 if event.id == id:
                   if event.type == 'artists':
                     artwork = event.artists[0].artist.cover.uri
                   if event.type == 'tracks':
                     artwork = event.tracks[0].cover_uri
                   if event.type == 'albums':
                     artwork = event.albums[0].album.cover_uri
                   artwork_uri = "https://"+artwork.replace("%%","400x400")
                   result[uri] = [models.Image(uri=artwork_uri)]

            if kind == "directory":
               if id == "root":
                 artwork_uri = "https://"+YMRef.root().artwork
                 result[uri] = [models.Image(uri=artwork_uri)]
            if kind == "track":
                track = self._track_cache.get(uri)
                artwork_uri = ""
                if track is None:
                    track = self._client.tracks(id)[0]
                    artwork_uri = track.cover_uri.replace("%%","%1x%2")
                else:
                    artwork_uri = track.artwork
                artwork_uri = "https://" + artwork_uri.replace("%1", "400").replace("%2", "400")
                result[uri] = [models.Image(uri=artwork_uri)]
            if kind == "album":
                album = self._client.albums(id)[0]
                artwork_uri = "https://" + album.cover_uri.replace("%%", "400x400")
                result[uri] = [models.Image(uri=artwork_uri)]
            if kind == "artist":
                artist = self._client.artists(id)[0]
                logger.error(artist)
                artwork_uri = "https://" + artist.cover.uri.replace("%%", "400x400")
                result[uri] = [models.Image(uri=artwork_uri)]
            if kind == "playlist":
                playlist_list = self._playlist_cache.get_list()
                for playlist in playlist_list:
                    if playlist.uri == uri:
                      artwork_uri = "https://" + playlist.artwork.replace("%%", "400x400")
                      result[uri] = [models.Image(uri=artwork_uri)]
                pass
        logger.error(result)
        return result
