from decimal import Decimal
import logging
import os
import json

import dateutil.parser
import requests
import configurations
from django.utils.timezone import now
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


class DigitalPourParser(BaseTapListProvider):
    """Parser for DigitalPour based vendors."""

    URL = 'https://mobile.digitalpour.com/DashboardServer/v4/MobileApp/MenuItems/{}/{}/Tap?ApiKey={}'  # noqa
    APIKEY = '574725e55e002c0b7cf0cf19'
    provider_name = 'digitalpour'

    def __init__(self, location=None):
        """Constructor."""
        self.url = None
        if location:
            self.url = self.URL.format(location[0], location[1], self.APIKEY)
        super().__init__()

    def handle_venue(self, venue):
        venue_id = venue.api_configuration.digital_pour_venue_id
        location_number = venue.api_configuration.digital_pour_location_number
        self.url = self.URL.format(venue_id, location_number, self.APIKEY)
        data = self.fetch()
        taps = {tap.tap_number: tap for tap in venue.taps.all()}
        manufacturers = {}
        for entry in data:
            if not entry['Active']:
                # in the cooler, not on tap
                continue
            # 1. parse the tap
            tap_info = self.parse_tap(entry)
            try:
                tap = taps[tap_info['tap_number']]
            except KeyError:
                tap = Tap(venue=venue, tap_number=tap_info['tap_number'])
            tap.time_added = tap_info['added']
            tap.time_updated = tap_info['updated']
            tap.estimated_percent_remaining = tap_info['percent_full']
            if tap_info['gas_type'] in [i[0] for i in Tap.GAS_CHOICES]:
                tap.gas_type = tap_info['gas_type']
            else:
                tap.gas_type = ''
            # 2. parse the manufacturer, creating if needed
            parsed_manufacturer = self.parse_manufacturer(entry)
            try:
                manufacturer = manufacturers[parsed_manufacturer['name']]
            except KeyError:
                defaults = {
                    field: parsed_manufacturer[field] for field in [
                        'location', 'logo_url', 'twitter_handle', 'url',
                    ] if parsed_manufacturer[field]
                }
                manufacturer = self.get_manufacturer(
                    name=parsed_manufacturer['name'],
                    **defaults,
                )
                manufacturers[manufacturer.name] = manufacturer
            # 3. get the beer, creating if necessary
            parsed_beer = self.parse_beer(entry)
            name = parsed_beer.pop('name')
            color_html = parsed_beer.pop('color', '')
            if color_html:
                # convert 0xabcde into #0abcde
                color_html = f'#{color_html[2:]:0>6}'
                parsed_beer['color_html'] = color_html
            else:
                # clear the color if unknown
                parsed_beer['color_html'] = ''
            LOG.debug(
                'looking up beer: name %s, mfg %s, other data %s',
                name, manufacturer, parsed_beer,
            )
            if name.casefold().strip() == 'N/A'.casefold():
                if not parsed_beer.get('abv'):
                    # it's an empty tap
                    LOG.info('Tap %s is unused', tap.tap_number)
                    tap.beer = None
                    tap.save()
                    continue
            beer = self.get_beer(
                name, manufacturer, pricing=self.parse_pricing(entry),
                venue=venue, **parsed_beer,
            )
            # 4. assign the beer to the tap
            tap.beer = beer
            tap.save()

    def parse_beer(self, entry):
        """Parse beer info from JSON entry."""
        detail = entry['MenuItemProductDetail']
        b = detail['Beverage']
        if 'Cider' in b['$type']:
            beer = {
                'name': b['CiderName'],
                'style': b['CiderStyle']['StyleName'],
                'abv': b['Abv'],
                'ibu': b['Ibu'],
                'color': hex(b['CiderStyle']['Color']),
                'logo_url': b.get('LogoImageUrl'),
                'beer_advocate_url': b.get('BeerAdvocateUrl'),
                'rate_beer_url': b.get('RateBeerUrl'),
                'manufacturer_url': b.get('BeerUrl'),
            }
        elif 'Mead' in b['$type']:
            beer = {
                'name': b['MeadName'],
                'style': b['MeadStyle']['StyleName'],
                'abv': b['Abv'],
                'ibu': b.get('Ibu'),
                'color': hex(b['MeadStyle']['Color']),
                'logo_url': b.get('LogoImageUrl'),
                'beer_advocate_url': b.get('BeerAdvocateUrl'),
                'rate_beer_url': b.get('RateBeerUrl'),
                'manufacturer_url': b.get('BeerUrl'),
            }
        elif 'Wine' in b['$type']:
            beer = {
                'name': b['WineName'],
                'style': b['FullStyleName'],
                'abv': b['Abv'],
                'ibu': b.get('Ibu'),
                'color': hex(b['StyleColor']),
                'logo_url': b.get('LogoImageUrl'),
                'beer_advocate_url': b.get('BeerAdvocateUrl'),
                'rate_beer_url': b.get('RateBeerUrl'),
                'manufacturer_url': b.get('BeerUrl'),
            }
        elif 'Kombucha' in b['$type']:
            beer = {
                'name': b['KombuchaName'],
                'style': b['FullStyleName'],
                'abv': b['Abv'],
                'ibu': b.get('Ibu'),
                'color': hex(b['StyleColor']),
                'logo_url': b.get('LogoImageUrl'),
                'beer_advocate_url': b.get('BeerAdvocateUrl'),
                'rate_beer_url': b.get('RateBeerUrl'),
                'manufacturer_url': b.get('BeerUrl'),
            }
        elif 'HardSeltzer' in b['$type']:
            beer = {
                'name': b['HardSeltzerName'],
                'style': b['HardSeltzerStyle']['StyleName'],
                'abv': b['Abv'],
                'ibu': b.get('Ibu', 0),
                'color': hex(b['StyleColor']),
                'logo_url': b.get('LogoImageUrl'),
                'beer_advocate_url': b.get('BeerAdvocateUrl'),
                'rate_beer_url': b.get('RateBeerUrl'),
                'manufacturer_url': b.get('BeerUrl'),
            }
        else:
            beer = {
                'name': b['BeerName'],
                'style': b['BeerStyle']['StyleName'],
                'abv': b['Abv'],
                'ibu': b['Ibu'],
                'color': hex(b['BeerStyle']['Color']),
                'beer_advocate_url': b.get('BeerAdvocateUrl'),
                'rate_beer_url': b.get('RateBeerUrl'),
                'manufacturer_url': b.get('BeerUrl'),
                'logo_url': b.get('LogoImageUrl') or b.get('ResolvedLogoImageUrl') or None,
            }
        return beer

    def parse_manufacturer(self, tap):
        """Parse manufacturer info from JSON entry."""
        producer = tap['MenuItemProductDetail']['Beverage']['BeverageProducer']

        styles = [
            'Cidery', 'Meadery', 'Winery', 'KombuchaMaker', 'Brewery', 'HardSeltzerMaker',
        ]
        url = ''
        for style in styles:
            try:
                name = producer[f'{style}Name']
            except KeyError:
                # try the next one
                continue
            else:
                url = producer.get(f'{style}Url', '') or ''
                # success
                break
        else:
            raise ValueError(f"Unknown producer type {producer}")

        manufacturer = {
            'name': name,
            'location': producer['Location'] or '',
            'logo_url': producer.get('LogoImageUrl'),
            'twitter_handle': producer.get('TwitterName') or '',
            'url': url,
        }
        if manufacturer['url'] and not manufacturer['url'].casefold().startswith(
            'http'.casefold()
        ):
            manufacturer['url'] = f'http://{manufacturer["url"]}'
        if manufacturer['twitter_handle']:
            if manufacturer['twitter_handle'].startswith('@'):
                # strip the leading @ for consistency
                manufacturer['twitter_handle'] = manufacturer['twitter_handle'][1:]
            if '/' in manufacturer['twitter_handle']:
                manufacturer['twitter_handle'] = manufacturer['twitter_handle'].rsplit('/', 1)[-1]
        LOG.debug(
            'Got twitter name %s from producer %s',
            manufacturer['twitter_handle'], producer,
        )
        return manufacturer

    def parse_tap(self, tap):
        """Parse tap info from JSON entry."""
        ret = {
            'added': dateutil.parser.parse(tap['DatePutOn']),
            'updated': now(),
            'tap_number': tap['MenuItemDisplayDetail']['DisplayOrder'],
            'percent_full': tap['MenuItemProductDetail']['PercentFull'],
            'gas_type': (tap['MenuItemProductDetail']['KegType'] or '').lower(),
        }
        return ret

    def parse_pricing(self, tap):
        """Parse pricing info from JSON entry."""
        pricing = []
        prices = tap['MenuItemProductDetail']['Prices']
        for price in prices:
            if not price.get('DisplayOnMenu'):
                continue
            p = {
                'volume_oz': Decimal(round(price['DisplaySize'], 1)),
                # 6oz --> 6 oz
                'name': f'{price["DisplayName"][:-2]} '
                f'{price["DisplayName"][-2:]}',
                'price': price['Price'],
                'per_ounce': price['Price'] / price['Size'],
            }
            pricing.append(p)
        return pricing

    def fetch(self):
        """Fetch the most recent taplist"""
        data = requests.get(self.url).json()
        return data

    def taps(self):
        """Return list of current taps"""
        ret = []
        data = self.fetch()
        for entry in data:
            if not entry['Active']:
                continue
            tap_info = self.parse_tap(entry)
            tap_info['beer'] = self.parse_beer(entry)
            tap_info['manufacturer'] = self.parse_manufacturer(entry)
            tap_info['pricing'] = self.parse_pricing(entry)
            ret.append(tap_info)
        return ret


if __name__ == '__main__':
    import argparse

    locations = {
        'sta': ('5761f0a45e002c13703ed811', 1),
        'wywbmad': ('57b130dd5e002c0388f8b686', 1),
        'wywb805': ('57b130dd5e002c0388f8b686', 2),
        'otbx': ('5502506cb3b70304a8f2e0d2', 1),
        'rccb': ('5aa1a8135e002c0924805971', 1),
        'bufeddies': ('5afe0f3a5e002c0b8060a5b8', 1),
        'rrmad': ('5d657d943527260064257abf', 1),
        'rrdowntown': ('5d657d943527260064257abf', 2),
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('--dump', action='store_true')
    parser.add_argument('--print-logo-url', action='store_true')
    parser.add_argument('location')
    args = parser.parse_args()

    t = DigitalPourParser(locations[args.location])

    if args.dump:
        print(json.dumps(t.fetch(), indent=4))
    else:
        for tap in t.taps():
            if args.print_logo_url:
                print(f'{tap["beer"]["name"]}\t{tap["beer"]["logo_url"]}')
            else:
                print(tap['beer']['name'])
