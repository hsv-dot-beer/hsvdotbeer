import json
import logging
import os

import dateutil.parser
import requests
from bs4 import BeautifulSoup
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

from beers.models import Manufacturer
from taps.models import Tap

LOG = logging.getLogger(__name__)


class UntappdParser(BaseTapListProvider):
    URL = 'https://business.untappd.com/locations/{}/themes/{}/js'
    SEARCH = 'container.innerHTML = "'
    provider_name = 'untappd'

    def __init__(self, location=None, theme=None, cats=None):
        self.location_url = None
        if location and theme:
            self.location_url = self.URL.format(location, theme)

        self.categories = cats or []
        super().__init__()

    def fetch_data(self):
        if not self.location_url:
            raise ValueError('You must configure the location URL')
        data = requests.get(self.location_url).text
        return data

    def handle_venue(self, venue):
        self.categories = venue.api_configuration.untappd_categories
        self.location_url = self.URL.format(
            venue.api_configuration.untappd_location,
            venue.api_configuration.untappd_theme,
        )
        data = self.fetch_data()
        self.parse_html_and_js(data)
        rooms = list(venue.rooms.all())
        if not rooms:
            raise ValueError(f'You must create a room for {venue} first.')
        if len(rooms) != 1:
            raise ValueError(
                f'Untappd does not support rooms! {len(rooms)} found',
            )
        room = rooms[0]

        taps = {tap.tap_number: tap for tap in room.taps.all()}
        manufacturers = {}
        tap_list = self.taps()
        use_sequential_taps = any(
            tap_info['tap_number'] is None for tap_info in tap_list
        )
        for index, tap_info in enumerate(tap_list):
            # 1. get the tap
            # if the venue doesn't give tap numbers, just use a 1-based
            # counter
            if use_sequential_taps:
                tap_number = index + 1
            else:
                tap_number = tap_info['tap_number']
            try:
                tap = taps[tap_number]
            except KeyError:
                tap = Tap(room=room, tap_number=tap_number)
            if tap_info['added']:
                tap.time_added = tap_info['added']
            if tap_info['updated']:
                tap.time_updated = tap_info['updated']
            # 2. parse the manufacturer
            try:
                manufacturer = manufacturers[tap_info['manufacturer']['name']]
            except KeyError:
                manufacturer = Manufacturer.objects.get_or_create(
                    name=tap_info['manufacturer']['name'],
                    defaults={'location': tap_info['manufacturer']['location']}
                )[0]
                manufacturers[manufacturer.name] = manufacturer
            # 3. get the beer, creating if necessary
            beer_name = tap_info['beer'].pop('name')
            # TODO (#37): map styles
            style = tap_info['beer'].pop('style', {})
            if style:
                tap_info['beer']['api_vendor_style'] = \
                    f"{style['category']} - {style['name']}"
            beer = self.get_beer(
                beer_name, manufacturer, **tap_info['beer']
            )
            # 4. assign the beer to the tap
            tap.beer = beer
            tap.save()

    def parse_html_and_js(self, data):
        # Pull the relevant HTML from the JS.
        start_idx = data.find(self.SEARCH)
        end_idx = data.find(';\n\n')
        html = data[(start_idx + len(self.SEARCH)):end_idx]

        # Unescape the HTML
        html = html.replace('\\n', '')
        html = html.replace('\\"', '"')
        html = html.replace('\\/', '/')
        html = html.replace("\\\'", "'")

        self.soup = BeautifulSoup(html, 'lxml')

        info_elements = self.soup.find_all('div', {'class': 'section'})

        self.taplists = []

        for element in info_elements:
            text = element.find('div', {'class': 'section-name'}).text
            if text in self.categories:
                self.taplists.append(element)

    def parse_style(self, style):
        if '-' in style:
            cat = style.split('-')[0].strip()
            name = style.split('-')[1].strip()
        else:
            cat = None
            name = style
        return {'name': name, 'category': cat}

    def parse_size(self, size):
        if size == '1/6 Barrel':
            return 660
        elif size == '1/4 Barrel':
            return 996
        elif size == '1/2 Barrel':
            return 1980
        else:
            return int(size.split('oz')[0])

    def parse_price(self, price):
        price = price.replace('$', '')
        return float(price)

    def parse_pricing(self, entry):
        pricing = []

        price_div = entry.find('div', {'class': 'with-price'})
        if price_div:
            for row in price_div.find_all('div', {'class': 'container-row'}):
                size = row.find('span', {'class': 'type'}).text
                price = row.find('span', {'class': 'price'}).text
                price = {
                    'size': self.parse_size(size),
                    'price': self.parse_price(price)
                }
                price['per_ounce'] = price['price'] / price['size']
                pricing.append(price)
        return pricing

    def parse_tap(self, entry):
        beer_info = entry.find('p', {'class': 'beer-name'}).text
        tap_num = entry.find('span', {'class': 'tap-number-hideable'}).text.strip()

        beer_style = entry.find('span', {'class': 'beer-style'}).text
        brewery = entry.find('span', {'class': 'brewery'}).text
        loc = entry.find('span', {'class': 'location'}).text

        beer_info = beer_info.replace(tap_num, '')
        beer_info = beer_info.replace(beer_style, '')
        beer_info = beer_info.strip()

        t = {
            'beer':
            {
                'name': beer_info,
                'style': self.parse_style(beer_style)
            },
            'manufacturer':
            {
                'name': brewery,
                'location': loc,
            },
            'pricing': self.parse_pricing(entry),
            'added': None,
            'updated': None,
            'tap_number': int(tap_num.replace('.', '')) if tap_num else None
        }

        abv = entry.find('span', {'class': 'abv'}).text
        abv = abv.replace('ABV', '')
        abv = float(abv.replace('%', ''))

        t['beer']['abv'] = abv

        ibu = entry.find('span', {'class': 'ibu'})
        if ibu:
            ibu = ibu.text.replace('IBU', '')
            ibu = float(ibu)
            t['beer']['ibu'] = ibu

        return t

    def taps(self):
        ret = []
        for taplist in self.taplists:
            entries = taplist.find_all('div', {'class': 'beer'})
            updated = None
            menus = self.soup.find_all('div', {'class': 'menu-info'})
            for menu in menus:
                if 'Tap List' in menu.text:
                    updated_str = menu.find('time').text
                    if updated_str.endswith('ST') or updated_str.endswith('DT'):
                        # it isn't in UTC. Grr.
                        # for now, just support CONUS time zones
                        tzinfos = {
                            'EST': -5 * 3600,
                            'EDT': -4 * 3600,
                            'CST': -6 * 3600,
                            'CDT': -5 * 3600,
                            'MST': -7 * 3600,
                            'MDT': -6 * 3600,
                            'PST': -8 * 3600,
                            'PDT': -7 * 3600,
                        }
                        updated = dateutil.parser.parse(updated_str, tzinfos=tzinfos)
                    else:
                        updated = dateutil.parser.parse(updated_str)
                    updated = updated.isoformat()

            for entry in entries:
                tap_info = self.parse_tap(entry)
                tap_info['updated'] = updated
                ret.append(tap_info)
        return ret


if __name__ == '__main__':
    import argparse

    LOCATIONS = {
        'dsb': ('3884', '11913', ['Tap List']),
        'cpp': ('18351', '69229', ['On Tap']),
        'yh': ('5949', '20074', ['YEAR-ROUND', 'SEASONALS', 'Beer']),
        'mm': ('8588', '30573', ['Favorites', 'Seasonals', 'Exclusives'])
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('--dump', action='store_true')
    parser.add_argument('location')
    args = parser.parse_args()

    t = UntappdParser(*LOCATIONS[args.location])
    data = t.fetch_data()
    t.parse_html_and_js(data)

    if args.dump:
        print(t.soup.prettify())

    for tap in t.taps():
        print(json.dumps(tap, indent=4))

    print(len(t.taps()))
