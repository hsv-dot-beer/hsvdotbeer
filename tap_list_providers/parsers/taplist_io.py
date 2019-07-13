#!/usr/bin/env python3
import os

from bs4 import BeautifulSoup
from dateutil.parser import parse
import requests
import configurations
from django.core.exceptions import ImproperlyConfigured, AppRegistryNotReady

# boilerplate code necessary for launching outside manage.py
try:
    from ..base import BaseTapListProvider
except (ImproperlyConfigured, AppRegistryNotReady):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'hsv_dot_beer.config'
    os.environ.setdefault("DJANGO_CONFIGURATION", "Local")
    configurations.setup()
    from ..base import BaseTapListProvider

from taps.models import Tap


class TaplistDotIOParser(BaseTapListProvider):
    """Class to represent a Taplist.io Display."""

    provider_name = 'taplist.io'
    URL = 'https://taplist.io/api/v1/displays/{0}'

    def __init__(self, display_id=None, taplist_access_code=None):
        super().__init__()
        self.display_id = display_id
        self.taplist_access_code = taplist_access_code
        self.on_tap = []
        self.on_deck = []
        self._data = None

    def fetch_data(self):
        response = requests.get(
            self.URL.format(self.display_id),
            cookies={'taplist_access_code': self.taplist_access_code},
            headers={
                'taplist-agent': 'TaplistClient/5',
                'user-agent': 'Python Requests - Alexa',
                'referer': 'https://taplist.io/display',
            },
        )
        self._data = response.json()

    def update(self):
        self.fetch_data()
        self.parse()

    def handle_venue(self, venue):
        self.display_id = venue.api_configuration.taplist_io_display_id
        self.taplist_access_code = venue.api_configuration.taplist_io_access_code
        self.fetch_data()
        taps = {i.tap_number: i for i in venue.taps.all()}
        timestamp = parse(self._data['date_modified'])
        for index, tap in enumerate(self._data['on_tap']):
            tap_dict = self.parse_tap(tap)
            tap_number = tap_dict.pop('tap_number', index + 1)
            current_tap = taps.get(
                tap_number, Tap(tap_number=tap_number, venue=venue))
            if not tap_dict:
                current_tap.beer = None
                current_tap.time_updated = timestamp
                current_tap.save()
                continue
            current_tap.time_added = tap_dict.pop('time_added')
            mfg_dict = tap_dict.pop('manufacturer')
            manufacturer = self.get_manufacturer(**mfg_dict)
            beer = self.get_beer(
                manufacturer=manufacturer, venue=venue,
                **tap_dict
            )
            current_tap.beer = beer
            if current_tap.time_updated != timestamp:
                current_tap.time_updated = timestamp
                current_tap.save()

    def parse_tap(self, tap_dict):
        if tap_dict['current_keg'] is None:
            return {}
        current = tap_dict['current_keg']['beverage']
        beverage = {}
        beverage['name'] = current['name']
        beverage['abv'] = current['abv_percent']
        beverage['color_srm'] = current.get('color_srm')
        beverage['color_html'] = current.get('color_hex', '') or ''
        beverage['logo_url'] = current.get('illustration_url')
        beverage['tap_number'] = tap_dict['current_keg']['current_tap_number']
        if beverage[
            'logo_url'
        ] and 'https://media.taplist.io/img/keg' in beverage['logo_url']:
            # Don't save the default logo
            beverage['logo_url'] = None
        if current['style']:
            beverage['style'] = current['style']['style']
        beverage['time_added'] = tap_dict['current_keg'].get('date_started')
        beverage['manufacturer'] = {
            'name': current['producer']['name'],
            'taplist_io_pk': current['producer']['id'],
            'url': current['producer'].get('url') or '',
        }
        beverage['taplist_io_pk'] = current['id']
        return beverage

    def parse(self):
        on_tap = []
        for d in self._data['on_tap']:
            beverage = self.parse_tap(d)
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
        display_id = int(resp.url.split('/')[-1])
        return (display_id, cookies['taplist_access_code'])

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
    td = TaplistDotIOParser(
        display_id='4434',
        taplist_access_code='5e5b8565-27b7-4cfd-8e52-b7d2b2ca5c63',
    )
    td.update()

    print(td.on_tap)
