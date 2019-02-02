import json

import datetime
import dateutil.parser
import requests

class DigitalPourParser:
    """Parser for DigitalPour based vendors."""

    URL = 'https://mobile.digitalpour.com/DashboardServer/v4/MobileApp/MenuItems/{}/{}/Tap?ApiKey={}'
    APIKEY = '574725e55e002c0b7cf0cf19'

    def __init__(self, location):
        """Constructor."""
        self.url = self.URL.format(location[0], location[1], self.APIKEY)

    def parse_beer(self, entry):
        """Parse beer info from JSON entry."""
        b = entry['MenuItemProductDetail']['Beverage']
        if 'Cider' in b['$type']:
            beer = {
                'name': b['CiderName'],
                'style': b['CiderStyle']['StyleName'],
                'abv': b['Abv'],
                'ibu': b['Ibu'],
                'color': hex(b['CiderStyle']['Color'])
            }
        else:
            beer = {
                'name': b['BeerName'],
                'style': b['BeerStyle']['StyleName'],
                'abv': b['Abv'],
                'ibu': b['Ibu'],
                'color': hex(b['BeerStyle']['Color'])
            }
        return beer

    def parse_manufacturer(self, tap):
        """Parse manufacturer info from JSON entry."""
        producer = tap['MenuItemProductDetail']['Beverage']['BeverageProducer']

        if 'CideryName' in producer:
            name = producer['CideryName']
        else:
            name = producer['BreweryName']

        manufacturer = {
            'name': name,
            'location': producer['Location']
        }
        return manufacturer

    def parse_tap(self, tap):
        """Parse tap info from JSON entry."""
        ret = {
            'added': dateutil.parser.parse(tap['DatePutOn']).isoformat(),
            'updated': datetime.datetime.utcnow().isoformat(),
            'tap_number': tap['MenuItemDisplayDetail']['DisplayOrder'],
            'percent_full': tap['MenuItemProductDetail']['PercentFull']
        }
        return ret

    def parse_pricing(self, tap):
        """Parse pricing info from JSON entry."""
        pricing = []
        prices = tap['MenuItemProductDetail']['Prices']
        for price in prices:
            p = {
                'size': price['Size'],
                'price': price['Price'],
                'per_ounce': price['Price']/price['Size']
            }
            pricing.append(p)
        return pricing


    def fetch(self):
        """Fetch the most recent taplist"""
        data = requests.get(self.url).text
        data = json.loads(data)
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
        'bufeddies': ('5afe0f3a5e002c0b8060a5b8', 1)
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('--dump', action='store_true')
    parser.add_argument('location')
    args = parser.parse_args()

    t = DigitalPourParser(locations[args.location])

    if args.dump:
        print(json.dumps(t.fetch(), indent=4))
    else:
        for tap in t.taps():
            print(tap['beer']['name'])
