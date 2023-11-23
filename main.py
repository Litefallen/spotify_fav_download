import httpx
import dotenv
import os
from os import path
import asyncio
import base64
import fastapi
import webbrowser
from fastapi import Query
from get_music import get_your_music
from fastapi.responses import RedirectResponse
import uvicorn

music_list = []


def folder_mk():
    cur_dir = os.getcwd()
    if not path.split(cur_dir)[1] == 'Music':
        if not os.path.exists('Music'):
            os.mkdir('Music')
    os.chdir("Music")


async def get_fav_songs(at, client, offset):
    track_resp = await client.get('https://api.spotify.com/v1/me/tracks',
                                  headers={'Authorization': f'Bearer {at['access_token']}'},
                                  params={'limit': '50', 'offset': offset})
    items = track_resp.json()['items']
    for i in items:
        artist = i.get('track').get('artists')[0]['name']
        track = i.get('track').get('name')
        # print( artist,track)
        music_list.append((artist, track))


dotenv.load_dotenv()
client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
api = fastapi.FastAPI()


@api.get('/end')
def end_page():
    return 'You may close this tab now'


@api.get('/callback/')
async def gett(code=Query):
    auth_code = code
    base64_auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {'Authorization': f'Basic {base64_auth}', 'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'grant_type': 'authorization_code', 'code': auth_code,
            'redirect_uri': 'http://127.0.0.1:8000/callback/'}
    req = httpx.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
    at = req.json()
    folder_mk()
    track_resp = httpx.get('https://api.spotify.com/v1/me/tracks',
                           headers={'Authorization': f'Bearer {at['access_token']}'},
                           params={'limit': '50', 'offset': 0}).json()
    total_amount = track_resp['total']
    num_cur_tracks = len(track_resp['items'])

    print(f"This is the total amount of favorited songs:{total_amount}")
    async with httpx.AsyncClient() as client:
        print('Getting fav songs list...')
        await asyncio.gather(
            *[get_fav_songs(at, client, 0 + 50 * c) for c in range(total_amount // num_cur_tracks + 1)])
    for i in music_list:
        await get_your_music(i[0], i[1])
    print('All songs were downloaded')
    return RedirectResponse('/end')
    # loop = asyncio.get_event_loop()
    # loop.stop()


if __name__ == "__main__":
    webbrowser.open(
        f'https://accounts.spotify.com/authorize?response_type=code&client_id={client_id}&redirect_uri=http://127.0.0.1:8000/callback/&scope=user-library-read&show_dialog=True')
    uvicorn.run("main:api", host="127.0.0.1", port=8000, log_level=None)
