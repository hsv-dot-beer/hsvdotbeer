"""Parse beers from TapHunter"""
import argparse
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

from taps.models import Tap


LOG = logging.getLogger(__name__)


class TaphunterParser(BaseTapListProvider):
    """Parser for TapHunter based vendors."""

    URL = 'https://www.taphunter.com/widgets/location/v3/{}.json'
    provider_name = 'taphunter'

    def __init__(self, location=None):
        """Constructor."""
        self.url = None
        self.json = {}
        if location:
            self.url = self.URL.format(location)
        super().__init__()

    def handle_venue(self, venue):
        location = venue.api_configuration.taphunter_location
        excluded_lists = venue.api_configuration.taphunter_excluded_lists
        self.url = self.URL.format(location)
        data = self.fetch()
        taps = {tap.tap_number: tap for tap in venue.taps.all()}
        manufacturers = {}

        use_sequential_taps = any(
            (tap_info['serving_info']['tap_number'] == '' for tap_info in data['taps'])
        )
        for index, entry in enumerate(data['taps']):
            # 1. parse the tap
            tap_info = self.parse_tap(entry)
            # Is it in an excluded list?
            if excluded_lists and entry.get('list', {'name': -1})['name'] in excluded_lists:
                LOG.debug(
                    'Skipping %s because it is in excluded list %s',
                    entry['beer']['beer_name'],
                    entry['list']['name'],
                )
                continue
            if use_sequential_taps:
                tap_number = index + 1
            else:
                tap_number = tap_info['tap_number']
            try:
                tap = taps[tap_number]
            except KeyError:
                tap = Tap(venue=venue, tap_number=tap_number)
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
                kwargs = {
                    key: val for key, val in parsed_manufacturer.items()
                    if key != 'name' and val
                }
                manufacturer = self.get_manufacturer(
                    name=parsed_manufacturer['name'],
                    **kwargs,
                )
                manufacturers[manufacturer.name] = manufacturer
            # 3. get the beer, creating if necessary
            parsed_beer = self.parse_beer(entry)
            name = parsed_beer['name']
            style = parsed_beer.pop('style', {})
            if style:
                parsed_beer['style'] = f"{style['category']} - {style['name']}"
            color_srm = parsed_beer.pop('srm', 0)
            if color_srm:
                parsed_beer['color_srm'] = color_srm
            LOG.debug(
                'looking up beer: name %s, mfg %s, other data %s',
                name, manufacturer, parsed_beer,
            )
            beer = self.get_beer(
                manufacturer=manufacturer, pricing=self.parse_pricing(entry),
                venue=venue, **parsed_beer,
            )
            # 4. assign the beer to the tap
            tap.beer = beer
            tap.save()

    def parse_beer(self, tap):
        beer = {
            'name': tap['beer']['beer_name'],
            'style': {
                'name': tap['beer']['style'],
                'category': tap['beer']['style_category'],
            },
            'logo_url': tap['beer'].get('logo_url') or tap['brewery'].get('logo_url') or None,
            'taphunter_url': tap['beer'].get('public_url') or None,
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
            'location': tap['brewery']['origin'],
            'logo_url': tap['brewery'].get('logo_url') or None,
            'taphunter_url': tap['brewery'].get('public_url') or None,
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
        return round(decimal.Decimal(price), 2)

    def parse_pricing(self, tap):
        pricing = []
        if 'serving_info' in tap:
            if 'sized_pricing' in tap['serving_info']:
                p = tap['serving_info']['sized_pricing']
                for entry in p:
                    price = {
                        'volume_oz': self.parse_size(entry['size']),
                        'name': entry['size'],
                        'price': self.parse_price(entry['price']),
                    }
                    price['per_ounce'] = price['price'] / price['volume_oz']
                    pricing.append(price)
        return pricing

    def fetch(self):
        data = requests.get(self.url).json()
        self.json = data
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


def main():
    """Simple console stuff"""
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


if __name__ == '__main__':
    main()
