import os
import spotipy
from datetime import datetime as dt
from spotipy.oauth2 import SpotifyOAuth
from utilities import Utilities as utils

ARTIST_PATH = os.path.join(".", "data", "{}")
ARTIST_URL_PREFIX = "https://open.spotify.com/artist/"

class SpotifyManager:
    def __init__(self, debug=False):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('clientID'),
            client_secret=os.getenv('clientSecret'),
            redirect_uri="http://localhost:8888/callback",
            scope="user-library-read,user-follow-read,playlist-modify-public,playlist-modify-private"))
        self.debug = debug

    def _get_artist_id_from_url(self, artist_id):
        if artist_id.startswith(ARTIST_URL_PREFIX):
            return artist_id[len(ARTIST_URL_PREFIX):len(ARTIST_URL_PREFIX) + 22]
        return artist_id

    def _save_response(self, path, data):
        utils.saveResponse(data, path)

    def getArtistCollabs(self, artist_id, force=False):
        artist_id = self._get_artist_id_from_url(artist_id)
        artist_folder = ARTIST_PATH.format(artist_id)

        if not force and os.path.exists(artist_folder):
            if self.debug:
                print("Already existed")
            return tuple(utils.loadJson(os.path.join(artist_folder, f"{name}.json")) for name in 
                        ["totalArtists", "registeredSongs", "lastCollab", "artistData", "artistProfileUrls"])

        os.makedirs(artist_folder, exist_ok=True)
        total_artists, registered_songs, last_collab_artist = {}, {}, {}
        ids_to_fetch = []
        artist_response = self.sp.artist(artist_id)
        artist_name = artist_response['name']
        offset = 0

        while True:
            response = self.sp.artist_albums(artist_id, album_type="album,single,appears_on", offset=offset)

            if not response.get('next'):
                all_artist_details = []
                for i in range(0, len(ids_to_fetch), 50):
                    ids_chunk = ids_to_fetch[i:i+50]
                    chunk_details = self.sp.artists(ids_chunk)
                    all_artist_details.extend(chunk_details['artists'])

                artists_details = {'artists': all_artist_details}
                
                artist_profile_urls = {artist['id']: artist['images'][0]['url'] if artist['images'] else None for artist in artists_details['artists']}
                self._save_response(os.path.join(artist_folder, "artistProfileUrls.json"), artist_profile_urls)

                last_collab_artist = {key: elem.strftime('%Y-%m-%d') for key, elem in last_collab_artist.items()}
                self._save_response(os.path.join(artist_folder, "totalArtists.json"), total_artists)
                self._save_response(os.path.join(artist_folder, "registeredSongs.json"), registered_songs)
                self._save_response(os.path.join(artist_folder, "lastCollab.json"), last_collab_artist)
                self._save_response(os.path.join(artist_folder, "artistData.json"), artist_response)
                return total_artists, registered_songs, last_collab_artist, artist_response, artist_profile_urls

            for album in response['items']:
                release_date_format = '%Y' if album["release_date_precision"] == "year" else '%Y-%m-%d'
                release_date = dt.strptime(album['release_date'], release_date_format)
                album_tracks = self.sp.album_tracks(album["uri"])

                for track in album_tracks['items']:
                    artists = [a["name"] for a in track['artists']]
                    if artist_name in artists:
                        track_list = registered_songs.setdefault(track["name"], [])
                        if artists not in track_list:
                            track_list.append(artists)
                        for artist in artists:
                            total_artists[artist] = total_artists.get(artist, 0) + 1
                            if artist_name != artist:
                                last_collab_artist[artist] = max(last_collab_artist.get(artist, release_date), release_date)
                                artist_id_to_add = track['artists'][artists.index(artist)]['id']
                                if artist_id_to_add not in ids_to_fetch:
                                    ids_to_fetch.append(artist_id_to_add)
            offset += 20  # len(response['items'])