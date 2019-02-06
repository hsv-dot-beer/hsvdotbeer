import json

import dateutil.parser
import requests
from bs4 import BeautifulSoup


class UntappdParser:
    URL = 'https://business.untappd.com/locations/{}/themes/{}/js'
    SEARCH = 'container.innerHTML = "'

    def __init__(self, location, theme, cats):
        self.location_url = self.URL.format(location, theme)
        data = requests.get(self.location_url).text

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
            if text in cats:
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
                    updated = dateutil.parser.parse(menu.find('time').text)
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

    if args.dump:
        print(t.soup.prettify())

    for tap in t.taps():
        print(json.dumps(tap, indent=4))
        pass

    print(len(t.taps()))
