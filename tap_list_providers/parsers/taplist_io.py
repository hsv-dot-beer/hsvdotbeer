#!/usr/bin/env python3

from bs4 import BeautifulSoup

import requests

import json


class TaplistDisplay:
    """Class to represent a Taplist.io Display."""

    def __init__(self, displayid, taplist_access_code):
        self.displayid = displayid
        self.taplist_access_code = taplist_access_code

        self.on_tap = []
        self.on_deck = []
        self._data = None

    def update(self):
        r = requests.get(
                'https://taplist.io/api/v1/displays/' + str(self.displayid),
                cookies={'taplist_access_code': self.taplist_access_code},
                headers={'taplist-agent': 'TaplistClient/5',
                         'user-agent': 'Python Requests - Alexa',
                         'referer': 'https://taplist.io/display'})
        print(json.dumps(r.json()['on_tap'], indent=4, sort_keys=True))
        self._data = r.json()
        self.parse()

    def parse(self):
        on_tap = []
        for d in self._data['on_tap']:
            if d['current_keg'] is None:
                continue
            current = d['current_keg']['beverage']
            beverage = {}
            beverage['name'] = current['name']
            beverage['abv'] = current['abv_percent']
            if current['style']:
                beverage['style'] = current['style']['style']
            on_tap.append(beverage)
        self.on_tap = on_tap


class TaplistAPI:
    """Class to represent Taplist.io API."""

    BASE_URL = 'https://taplist.io/'
    LOGIN_URL = BASE_URL + 'account/login/'
    DISPLAY_URL = BASE_URL + 'display'
    API_URL = BASE_URL + 'api/v1/'
    API_LOGIN_URL = API_URL + 'api-auth/login/'
    LINK_URL = BASE_URL + 'dashboard/displays/link/'

    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.login_r = self._login()
        self.api_r = self._api_login()

    def create_display(self):
        code, cookies = self._get_pairing_code()
        activate = requests.get(
                self.LINK_URL,
                cookies={'sessionid': self.login_r.cookies['sessionid'],
                         'csrftoken': self.login_r.cookies['csrftoken']})
        soup = BeautifulSoup(activate.text, 'html.parser')
        csrftag = soup.find_all(attrs={'name': 'csrfmiddlewaretoken'})[0]
        csrftag = csrftag.attrs['value']

        resp = requests.post(
                self.LINK_URL,
                cookies={'sessionid': self.login_r.cookies['sessionid'],
                         'csrftoken': self.login_r.cookies['csrftoken']},
                data={'csrfmiddlewaretoken': csrftag,
                      'code': code},
                headers={'referer': self.LINK_URL,
                         'origin': self.BASE_URL})
        displayid = int(resp.url.split('/')[-1])
        return (displayid, cookies['taplist_access_code'])


    def _get_pairing_code(self):
        r = requests.get(self.DISPLAY_URL)
        soup = BeautifulSoup(r.text, 'html.parser')
        tag = soup.find_all('h1', 'pairing-code')[0]
        cookies = requests.utils.dict_from_cookiejar(r.cookies)
        return (tag.text, cookies)

    def _login(self):
        r1 = requests.get(self.LOGIN_URL)
        self.csrftoken = r1.cookies['csrftoken']
        login_data = {'username': self.username,
                      'password': self.password,
                      'csrfmiddlewaretoken': self.csrftoken}
        r2 = requests.post(self.LOGIN_URL,
                           data=login_data,
                           cookies=r1.cookies,
                           headers={'referer': self.LOGIN_URL})
        return r2

    def _api_login(self):
        r1 = requests.get(self.API_LOGIN_URL)
        self.api_csrftoken = r1.cookies['csrftoken']
        login_data = {'username': self.username,
                      'password': self.password,
                      'csrfmiddlewaretoken': self.api_csrftoken,
                      'next': '/api/v1'}

        r2 = requests.post(self.API_LOGIN_URL,
                           data=login_data,
                           cookies=r1.cookies,
                           headers={'referer': self.LOGIN_URL})
        self.api_session_id = r2.cookies['sessionid']
        return r2


if __name__ == '__main__':
    td = TaplistDisplay(displayid='4434', taplist_access_code='5e5b8565-27b7-4cfd-8e52-b7d2b2ca5c63')
    td.update()

    print(td.on_tap)
