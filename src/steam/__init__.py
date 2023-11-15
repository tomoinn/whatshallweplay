from dataclasses import dataclass
from functools import cache

import requests


@dataclass
class User:
    steamid: str
    personaname: str
    avatar: str
    avatarmedium: str
    avatarfull: str

    @staticmethod
    def from_json(u) -> 'User':
        return User(steamid=u['steamid'], personaname=u['personaname'].lower(), avatar=u['avatar'],
                    avatarmedium=u['avatarmedium'], avatarfull=u['avatarfull'])


@dataclass
class Game:
    name: str
    categories: set[str]

    @staticmethod
    def from_json(g) -> 'Game':
        return Game(name=g['name'], categories=set([c['description'].lower() for c in g['categories']]))


class SteamAPI:

    def __init__(self, key: str, steam_id: str):
        self._key = key
        self._steam_id = steam_id

    @cache
    def friends(self, steam_id=None) -> list[User]:
        url = 'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/'
        r = requests.get(url=url, params={'key': self._key, 'steamid': steam_id or self._steam_id, 'format': 'json'})
        friend_ids = [f['steamid'] for f in r.json()['friendslist']['friends']]
        url = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/'
        r = requests.get(url=url, params={'key': self._key, 'format': 'json', 'steamids': ','.join(friend_ids)})
        return [User.from_json(u) for u in r.json()['response']['players']]

    @cache
    def owned_games(self, steam_id=None) -> list[int]:
        url = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/'
        r = requests.get(url=url, params={'key': self._key, 'steamid': steam_id or self._steam_id, 'format': 'json'})
        appids = [g['appid'] for g in r.json()['response']['games']]
        return appids

    def games_in_common(self, persona_list: list[str]) -> list[int]:
        games = set(self.owned_games())
        for user in self.friends():
            if user.personaname in persona_list:
                friend_games = set(self.owned_games(steam_id=user.steamid))
                print(f'comparing games with {user.personaname}')
                games = games & friend_games
        print(f'{len(games)} games in common')
        return list(games)

    @cache
    def app_details(self, appid: int):
        url = 'http://store.steampowered.com/api/appdetails'
        r = requests.get(url=url, params={'appids': str(appid)})
        details = r.json()[str(appid)]
        if 'data' in details:
            return Game.from_json(details['data'])
        else:
            print(f'unable to fetch for game ID {appid}')
            return Game(name='', categories=set())


api = SteamAPI(key='B338655D3DCBB94EACDEFBCBD001EDC0', steam_id='76561197970430959')
games_in_common = [api.app_details(appid) for appid in api.games_in_common(persona_list=['brey'])]
print(f'co-op games in common', [game.name for game in games_in_common if 'online co-op' in game.categories])
