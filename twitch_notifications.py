import requests
import json
from urllib.parse import quote

config = json.load(open('config.json'))


class Stream:
    def __init__(self, title, streamer, game, thumbnail_url):
        self.title = title
        self.streamer = streamer
        self.game = game
        self.thumbnail_url = thumbnail_url

    def __str__(self):
        return (f"Title: {self.title}\n"
                f"Streamer: {self.streamer}\n"
                f"Game: {self.game}\n"
                f"Thumbnail URL: {self.thumbnail_url}")


def getOAuthToken():
    body = {
        "client_id": config['client_id'],
        "client_secret": config['client_secret'],
        "grant_type": "client_credentials"
    }
    r = requests.post('https://id.twitch.tv/oauth2/token', json=body)

    if r.status_code != 200:
        raise Exception(f"Failed to get OAuth token: {r.status_code} {r.text}")

    keys = r.json()
    return keys['access_token']


def checkIfLive(channel):
    encoded_channel = quote(channel)  # Кодируем имя канала
    url = f"https://api.twitch.tv/helix/streams?user_login={encoded_channel}"
    token = getOAuthToken()

    HEADERS = {
        'Client-ID': config['client_id'],
        'Authorization': f'Bearer {token}'
    }

    try:
        req = requests.get(url, headers=HEADERS)

        if req.status_code != 200:
            raise Exception(f"Failed to get stream data: {req.status_code} {req.text}")

        res = req.json()

        if 'data' in res and len(res['data']) > 0:  # Проверяем, что стример онлайн
            data = res['data'][0]
            title = data.get('title', 'No Title')
            streamer = data.get('user_name', 'No Streamer')
            game = data.get('game_name', 'No Game')
            # Заменяем переменные в URL на фиксированные размеры
            thumbnail_url = data.get('thumbnail_url', 'No Thumbnail').replace('{width}', '1920').replace('{height}',
                                                                                                         '1080')
            stream = Stream(title, streamer, game, thumbnail_url)
            return stream
        else:
            return "OFFLINE"
    except Exception as e:
        return f"An error occurred: {str(e)}"
