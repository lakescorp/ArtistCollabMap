import os
import spotipy
from datetime import datetime as dt
from spotipy.oauth2 import SpotifyOAuth
from utilities import Utilities as utils
from dotenv import load_dotenv

ARTIST_PATH = os.path.join(".", "data", "{}")
ARTIST_URL_PREFIX = "https://open.spotify.com/artist/"

class SpotifyManager:
    def __init__(self, debug=False):
        load_dotenv()
        client_id = os.getenv('clientID')
        client_secret = os.getenv('clientSecret')

        if not client_id or not client_secret:
            raise EnvironmentError("Environment variables 'clientID' or 'clientSecret' not found.")


        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri="http://localhost:8888/callback",
                scope="user-library-read,user-follow-read,playlist-modify-public,playlist-modify-private"))
        except Exception as e:
            raise RuntimeError("Error authenticating with Spotify: " + str(e))    
        self.debug = debug
        print("Spotify working")


    def _get_artist_id_from_url(self, artist_id):
        if artist_id.startswith(ARTIST_URL_PREFIX):
            return artist_id[len(ARTIST_URL_PREFIX):len(ARTIST_URL_PREFIX) + 22]
        return artist_id

    def _save_response(self, path, data):
        utils.saveResponse(data, path)

    def search_artist(self, query, limit=1):
        """
        Search for an artist by name.
        
        Parameters:
        - query: The search string for the artist name.
        - limit: The number of results to return. Defaults to 1.
        
        Returns the first artist ID from the results or None if no results.
        """
        results = self.sp.search(q=query, limit=limit, type='artist')
        items = results.get('artists', {}).get('items', [])
        
        return items[0]['id'] if items else None

    def getArtistCollabs(self, artist_id, force=False):
        """
        Retrieves the artist collaborations for a given artist ID or name.

        Args:
            artist_id (str): The ID or name of the artist.
            force (bool, optional): If True, forces the retrieval of artist collaborations even if the data already exists. 
                                    Defaults to False.

        Returns:
            tuple: A tuple containing the following information:
                - total_artists (dict): A dictionary mapping artist IDs to the number of collaborations.
                - registered_songs (dict): A dictionary mapping track IDs to track information.
                - last_collab_artist (dict): A dictionary mapping artist IDs to the date of their last collaboration.
                - artist_response (dict): Information about the artist.
                - artists_info (dict): Information about the collaborating artists.
        """
        # First, we'll attempt to determine if the input is a name or ID.
        # If the input does not start with the Spotify URL prefix and does not seem to have the format of a Spotify ID,
        # then we'll assume it's a name and try to search for it.
        if not (artist_id.startswith(ARTIST_URL_PREFIX) or len(artist_id) == 22):
            searched_artist_id = self.search_artist(artist_id)
            if not searched_artist_id:
                raise ValueError(f"No artist found for the query: {artist_id}")
            artist_id = searched_artist_id


        seen_preview_urls = set()

        artist_id = self._get_artist_id_from_url(artist_id)
        artist_folder = ARTIST_PATH.format(artist_id)

        if not force and os.path.exists(artist_folder):
            if self.debug:
                print("Already existed")
            return tuple(utils.loadJson(os.path.join(artist_folder, f"{name}.json")) for name in 
                        ["totalArtists", "registeredSongs", "lastCollab", "artistData", "artistInfo"])

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
                
                artists_info = {artist['id']: {"name": artist['name'],
                               "url": artist['images'][0]['url'] if artist['images'] else None, 
                               "genres": artist['genres'] if 'genres' in artist else []} for artist in artists_details['artists']}           

                artists_info[artist_id] = {
                    'name': artist_name,
                    'url': artist_response['images'][0]['url'] if artist_response['images'] else None,
                    'genres': artist_response['genres']
                }

                last_collab_artist = {key: elem.strftime('%Y-%m-%d') for key, elem in last_collab_artist.items()}
                self._save_response(os.path.join(artist_folder, "totalArtists.json"), total_artists)
                self._save_response(os.path.join(artist_folder, "registeredSongs.json"), registered_songs)
                self._save_response(os.path.join(artist_folder, "lastCollab.json"), last_collab_artist)
                self._save_response(os.path.join(artist_folder, "artistData.json"), artist_response)
                self._save_response(os.path.join(artist_folder, "artistInfo.json"), artists_info)
                return total_artists, registered_songs, last_collab_artist, artist_response, artists_info

            for album in response['items']:
                release_date_format = '%Y' if album["release_date_precision"] == "year" else '%Y-%m-%d'
                release_date = dt.strptime(album['release_date'], release_date_format)
                album_tracks = self.sp.album_tracks(album["uri"])

                for track in album_tracks['items']:
                    if track['preview_url'] in seen_preview_urls:
                        continue
                    seen_preview_urls.add(track['preview_url'])
                    artist_ids = [a["id"] for a in track['artists']]
                    if artist_id in artist_ids:
                        track_data = registered_songs.setdefault(track["id"], {
                            "name": track["name"],
                            "url": album["external_urls"]["spotify"],
                            "artists": artist_ids,
                            "collaborations": [],
                            "thumbnail": album["images"][1]["url"],
                            "preview": track["preview_url"]
                        })
                        if artist_ids not in track_data["collaborations"]:
                            track_data["collaborations"].append(artist_ids)
                        for a_id in artist_ids:
                            total_artists[a_id] = total_artists.get(a_id, 0) + 1
                            if artist_id != a_id:
                                last_collab_artist[a_id] = max(last_collab_artist.get(a_id, release_date), release_date)
                                if a_id not in ids_to_fetch:
                                    ids_to_fetch.append(a_id)
            offset += 20 
