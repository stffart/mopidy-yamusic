## Mopidy-YaMusic

[Mopidy](https://mopidy.com) extension for playing music from
[Yandex Music](https://music.yandex.ru).

Extended version of https://pypi.org/project/Mopidy-Yandexmusic/ with some additional features.
***************
Features:
- Playback from YandexMusic
- Search: Artist, Track, Album
- Playlists: Generated Daily, Alice, Podcasts, Premier, Liked (Random from liked Tracks), Last Liked, Try (Daily Recommendations)
- User's stored playlists, add/remove track from playlist, like tracks
- Browse Daily Events (Yandex Recommendations)
- Local Track Cache

### Installation

Install by running:

```
pip install mopidy-yamusic
```

### Configuration

```
[yamusic]
bitrate = 192 
```

After restart go to http://mopidy:6680/yamusic, to authorize mopidy with yandex music api
