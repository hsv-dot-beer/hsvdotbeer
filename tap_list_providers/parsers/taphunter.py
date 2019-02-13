import json

import requests

locations = {
    'wholefoods': '5963904507707392',
    'lexpress': '6200813693698048',
    'wagonwheel': '6082279375634432'
}


class TaphunterParser:
    URL = 'https://www.taphunter.com/widgets/location/v3/'

    def __init__(self, location):
        self.location_url = self.URL + location + '.json'
        data = requests.get(self.location_url).text
        self.json = json.loads(data)

    def taps(self):
        ret= []
        for tap in self.json['taps']:
            tap_info = {
                "added": tap['date_added_iso8601'],
                "updated": tap['location']['update_timestamp_iso8601'],
                "beer": {
                    "name": tap['beer']['beer_name'],
                    "manufacturer": {
                        "name": tap['brewery']['name'],
                        "location": tap['brewery']['origin']
                    },
                    "style": {
                        "name": tap['beer']['style'],
                        "category": tap['beer']['style_category'],
                    }
                }
            }

            if tap['serving_info']['tap_number']:
                tap_info['tap_number'] = tap['serving_info']['tap_number']

            if tap['beer']['abv']:
                tap_info['beer']['abv'] = float(tap['beer']['abv'])

            if tap['beer']['srm']:
                tap_info['beer']['srm'] = int(tap['beer']['srm'])

            if tap['beer']['ibu']:
                tap_info['beer']['ibu'] = float(tap['beer']['ibu'])

            ret.append(tap_info)
        return ret

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--dump', action='store_true')
    parser.add_argument('location')
    args = parser.parse_args()

    t = TaphunterParser(locations[args.location])

    if args.dump:
        print(json.dumps(t.json, indent=4))
    else:
        for tap in t.taps():
            print(tap)



