

import os
import subprocess
import shlex
import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# setup environment variables from EnvVarMaster
CLIENT_ID = os.environ.get('CLIENT_ID', 'Client ID does not exist')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET', 'Client Secret does not exist')
REDIRECT_URI = os.environ.get('REDIRECT_URI', 'Redirect URI does not exist')
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', 'Access Token does not exist')

# constants and initial setup moved below environment variable setup
scope = "playlist-modify-private"
user_date_input = input(
    "I have a secret... 🤫 I have access to a Magical JukeBox which can Time Travel to the day a song became popular. Please type a chosen date in this format: YYYY-MM-DD: ")

# spotipy setup for spotify web api access
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=scope))

def fetch_songs_and_artists():
    response = requests.get(f"https://www.billboard.com/charts/hot-100/{user_date_input}/")
    if response.status_code != 200:
        print("Failed to retrieve data")
        exit()

    soup = BeautifulSoup(response.text, 'html.parser')
    songs_and_artists = []

    current_title = None
    for element in soup.find_all(["h3", "span"], class_=["c-title", "c-label"]):
        if 'c-title' in element['class']:
            title_text = element.get_text(strip=True)
            current_title = title_text if title_text and all(
                keyword not in title_text for keyword in ['Songwriter', 'Producer']) else None
        elif 'c-label' in element['class'] and current_title:
            artist_name_text = element.get_text(strip=True)
            if all(char.isdigit() is False for char in artist_name_text):
                songs_and_artists.append((current_title, artist_name_text))
                current_title = None

    return songs_and_artists


def attempt_playback(track_uri, track_url):
    try:
        # Attempt to play the track via Spotify Web API
        endpoint = "https://api.spotify.com/v1/me/player/play"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}  # Ensure you have a valid access token here
        data = {"uris": [track_uri]}
        response = requests.put(endpoint, headers=headers, json=data)
        if response.status_code == 204:
            print("Playback started successfully via Spotify Web API.")
            return
    except Exception as e:
        print("Failed to start playback via Web API:", e)

    try:
        # Attempt to open the Spotify URI with the desktop app
        subprocess.run(["spotify", "--uri=" + track_uri], check=True)
        print("Opening track in Spotify app...")
    except subprocess.CalledProcessError:
        print("Failed to open track in Spotify app, trying to open in browser...")
        # If opening in the Spotify app fails, open the track URL in a browser
        subprocess.run(["xdg-open", track_url], check=True)
        print("Opening song in browser...")

# main execution flow
songs_and_artists = fetch_songs_and_artists()
print(f"\nSongs and Artists from {user_date_input}:")
for i, (song, artist) in enumerate(songs_and_artists, start=1):
    print(f"Song {i}: {song}, Artist {i}: {artist}")

found_song = False
while not found_song:
    user_selection = int(input("\nEnter the song number you wish to play: "))
    if 1 <= user_selection <= len(songs_and_artists):
        selected_song, selected_artist = songs_and_artists[user_selection - 1]
        query = f"track:{selected_song} artist:{selected_artist}"
        result = sp.search(q=query, type="track")

        if result['tracks']['items']:
            found_song = True
            track_url = result['tracks']['items'][0]['external_urls']['spotify']
            track_uri = result['tracks']['items'][0]['uri']
            print(f"The URL for this song is: {track_url}\n")  # Print the Spotify URL
            print(f"The URI for this song is: {track_uri}\n")  # Print the Spotify URI

            attempt_playback(track_uri, track_url)  # Adjusted to pass track_url as a fallback
        else:
            print("Unfortunately, the song is not available right now. Please try another selection: ")
    else:
        print("Invalid selection. Please try again.")
