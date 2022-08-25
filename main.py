import datetime
from bs4 import BeautifulSoup
import requests
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# billboard 100 url
BILLBOARD_URL = "https://www.billboard.com/charts/hot-100/"

# spotify client id, client secret, & redirect uri for OAuth 
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# required scope for creating & modifying playlists
SCOPE = "playlist-modify-private"

# spotify base endpoint
SPOTIFY_BASE_URL = "https://api.spotify.com"

# access token
ACCESS_TOKEN = "paste-access-token-here"


def check_date(date_input):
    # check date input format is YYYY-MM-DD
    try:
        datetime.datetime.strptime(date_input, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def get_input():
    # get date input from user
    response = input("Enter the date in the following format: YYYY-MM-DD:\n")
    return response


def get_billboard_data(user_date):
    # get html data from billboard url
    page_response = requests.get(BILLBOARD_URL + user_date)
    return page_response.text


def make_soup(webpage):
    # parse billboard html response
    soup = BeautifulSoup(webpage, "html.parser")
    return soup


def get_top_songs(p_page):
    # return top 100 songs in list
    first_song = p_page.find(name='h3',
                             class_="c-title a-no-trucate a-font-primary-bold-s u-letter-spacing-0021 u-font-size-23@tablet lrv-u-font-size-16 u-line-height-125 u-line-height-normal@mobile-max a-truncate-ellipsis u-max-width-245 u-max-width-230@tablet-only u-letter-spacing-0028@tablet").text.strip()
    top_songs_list = [song.getText().strip() for song in p_page.find_all(name='h3',
                                                                         class_="c-title a-no-trucate a-font-primary-bold-s u-letter-spacing-0021 lrv-u-font-size-18@tablet lrv-u-font-size-16 u-line-height-125 u-line-height-normal@mobile-max a-truncate-ellipsis u-max-width-330 u-max-width-230@tablet-only")]
    top_songs_list.insert(0, first_song)
    return top_songs_list


def authenticate():
    # authenticate user
    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        show_dialog=True,
        cache_path="token.txt",
        scope=SCOPE)
    )

    return spotify


def create_playlist(name, public, uid):
    # create playlist
    response = requests.post(
        f"{SPOTIFY_BASE_URL}/v1/users/{uid}/playlists",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        },
        json={
            "name": name,
            "public": public
        }
    )
    json_resp = response.json()

    return json_resp


def add_playlist_items(playlist_id, uris_list):
    # add songs to playlist
    response = requests.post(
        f"{SPOTIFY_BASE_URL}/v1/playlists/{playlist_id}/tracks",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        },
        json={
            "uris": uris_list
        }
    )
    json_resp = response.json()

    return json_resp


def main():
    # get user response in yyyy-mm-dd format
    user_response = get_input()
    # check input format
    if check_date(user_response):
        # return html data from billboard url
        billboard_webpage = get_billboard_data(user_response)
        # parse html data
        parsed_page = make_soup(billboard_webpage)
        # store top 100 songs for given date to list
        top_100_songs = get_top_songs(parsed_page)

        # authentication
        spotify = authenticate()

        # get current user id
        user_id = spotify.current_user()["id"]

        # create playlist
        playlist = create_playlist(name=f"{user_response} Billboard 100",
                                   public=False,
                                   uid=user_id)

        # get year from user response
        year = user_response.split("-")[0]

        # create list to hold uris
        uris_list = []

        # get song uris & append to uris list
        for song in top_100_songs:
            result = spotify.search(q=f"track:{song} year:{year}", type="track")
            try:
                uri = result["tracks"]["items"][0]["uri"]
                uris_list.append(uri)
            except IndexError as e:
                print(e)

        # assign playlist id to variable
        playlist_id = playlist['id']

        # add songs list to playlist
        add_playlist_items(playlist_id, uris_list)


# entry point to program
if __name__ == "__main__":
    main()
