import decimal
import logging
import os
import json

import configurations
import requests
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


class TaphunterParser(BaseTapListProvider):
    """Parser for TapHunter based vendors."""

    URL = 'https://www.taphunter.com/widgets/location/v3/{}.json'
    provider_name = 'taphunter'

    def __init__(self, location=None):
        """Constructor."""
        self.url = None
        if location:
            self.url = self.URL.format(location)
        super().__init__()

    def handle_venue(self, venue):
        location = venue.api_configuration.taphunter_location
        self.url = self.URL.format(location)
        data = self.fetch()
        rooms = list(venue.rooms.all())
        if not rooms:
            raise ValueError(f'You must create a room for {venue} first.')
        if len(rooms) != 1:
            raise ValueError(
                f'TapHunter does not support rooms! {len(rooms)} found',
            )
        room = rooms[0]
        taps = {tap.tap_number: tap for tap in room.taps.all()}
        manufacturers = {}

        use_sequential_taps = any(
            (tap_info['serving_info']['tap_number'] == '' for tap_info in data['taps'])
        )
        for index, entry in enumerate(data['taps']):
            # 1. parse the tap
            tap_info = self.parse_tap(entry)
            if use_sequential_taps:
                tap_number = index + 1
            else:
                tap_number = tap_info['tap_number']
            try:
                tap = taps[tap_number]
            except KeyError:
                tap = Tap(room=room, tap_number=tap_number)
            tap.time_added = tap_info['added']
            tap.time_updated = tap_info['updated']
            if 'percent_full' in tap_info:
                tap.estimated_percent_remaining = tap_info['percent_full']
            else:
                tap.estimated_percent_remaining = None

            if 'gas_type' in tap_info and tap_info['gas_type'] in [i[0] for i in Tap.GAS_CHOICES]:
                tap.gas_type = tap_info['gas_type']
            else:
                tap.gas_type = ''
            # 2. parse the manufacturer, creating if needed
            parsed_manufacturer = self.parse_manufacturer(entry)
            try:
                manufacturer = manufacturers[parsed_manufacturer['name']]
            except KeyError:
                manufacturer = Manufacturer.objects.get_or_create(
                    name=parsed_manufacturer['name'],
                    defaults={
                        'location': parsed_manufacturer['location'],
                    }
                )[0]
                manufacturers[manufacturer.name] = manufacturer
            # 3. get the beer, creating if necessary
            parsed_beer = self.parse_beer(entry)
            name = parsed_beer.pop('name')
            # TODO (#37): map styles
            style = parsed_beer.pop('style', {})
            if style:
                parsed_beer['api_vendor_style'] = \
                    f"{style['category']} - {style['name']}"
            # TODO (#38): handle color
            color_srm = parsed_beer.pop('srm', '')
            if color_srm:
                parsed_beer['color_srm'] = color_srm
            LOG.debug(
                'looking up beer: name %s, mfg %s, other data %s',
                name, manufacturer, parsed_beer,
            )
            beer = self.get_beer(name, manufacturer, **parsed_beer)
            # 4. assign the beer to the tap
            tap.beer = beer
            tap.save()

    def parse_beer(self, tap):
        beer = {
            'name': tap['beer']['beer_name'],
            'style': {
                'name': tap['beer']['style'],
                'category': tap['beer']['style_category'],
            }
        }

        if tap['beer']['abv']:
            beer['abv'] = decimal.Decimal(tap['beer']['abv'])

        if tap['beer']['srm']:
            beer['srm'] = int(tap['beer']['srm'])

        if tap['beer']['ibu']:
            beer['ibu'] = float(tap['beer']['ibu'])

        return beer

    def parse_manufacturer(self, tap):
        manufacturer = {
            'name': tap['brewery']['name'],
            'location': tap['brewery']['origin']
        }
        return manufacturer

    def parse_tap(self, tap):
        t = {
            'added': tap['date_added_iso8601'],
            'updated': tap['location']['update_timestamp_iso8601']
        }
        if tap['serving_info']['tap_number']:
            t['tap_number'] = tap['serving_info']['tap_number']
        return t

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

    def parse_pricing(self, tap):
        pricing = []
        if 'serving_info' in tap:
            if 'sized_pricing' in tap['serving_info']:
                p = tap['serving_info']['sized_pricing']
                for entry in p:
                    price = {
                        'size': self.parse_size(entry['size']),
                        'price': self.parse_price(entry['price'])
                    }
                    price['per_ounce'] = price['price'] / price['size']
                    pricing.append(price)
        return pricing

    def fetch(self):
        data = requests.get(self.url).json()
        return data

    def taps(self):
        ret = []
        for tap in self.json['taps']:
            tap_info = self.parse_tap(tap)
            tap_info['beer'] = self.parse_beer(tap)
            tap_info['manufacturer'] = self.parse_manufacturer(tap)
            tap_info['pricing'] = self.parse_pricing(tap)
            ret.append(tap_info)
        return ret


if __name__ == '__main__':
    import argparse

    locations = {
        'wholefoods': '5963904507707392',
        'lexpress': '6200813693698048',
        'wagonwheel': '6082279375634432',
        'openbottle': '6032598809837568',
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('--dump', action='store_true')
    parser.add_argument('location')
    args = parser.parse_args()

    t = TaphunterParser(locations[args.location])

    if args.dump:
        print(json.dumps(t.json, indent=4))
    else:
        for tap in t.taps():
            print(json.dumps(tap, indent=4))
