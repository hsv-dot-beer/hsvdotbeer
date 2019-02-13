import json

import requests


class TaphunterParser:
    URL = 'https://www.taphunter.com/widgets/location/v3/'

    def __init__(self, location):
        self.location_url = self.URL + location + '.json'
        data = requests.get(self.location_url).text
        self.json = json.loads(data)

    def parse_beer(self, tap):
        beer = {
            'name': tap['beer']['beer_name'],
            'style': {
                'name': tap['beer']['style'],
                'category': tap['beer']['style_category'],
            }
        }

        if tap['beer']['abv']:
            beer['abv'] = float(tap['beer']['abv'])

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
        'wagonwheel': '6082279375634432'
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
