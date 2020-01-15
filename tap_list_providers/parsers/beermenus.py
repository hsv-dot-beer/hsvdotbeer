from decimal import Decimal
from dataclasses import dataclass
import logging
import os
from typing import List, Union

from dateutil.parser import parse
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from pytz import UTC
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


from venues.models import Venue
from taps.models import Tap

LOG = logging.getLogger(__name__)
MIDDOT = chr(183)


@dataclass
class BeerData:
    price: int
    serving_size: int
    url: str
    style: str
    abv: str
    brewery_name: str
    brewery_slug: str
    brewery_location: str
    name: str


class BeerMenusParser(BaseTapListProvider):
    URL = 'https://www.beermenus.com/places/{}'
    provider_name = 'beermenus'
    REQUEST_HEADERS = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
        'image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    }
    # the server barfs at us (422) if we don't include the x-requested-with
    # header
    XHR_HEADERS = {
        'x-requested-with': 'XMLHttpRequest',
        'accept': '*/*;q=0.5, text/javascript, application/javascript,'
        ' application/ecmascript, application/x-ecmascript',
    }
    DUMP_STORAGE_PATH = os.path.join(
        'tap_list_providers',
        'example_data',
        'beermenus'
    )

    def __init__(
        self,
        slug: Union[str, None] = None,
        categories: Union[List[str], None] = None,
        save_fetched_data: bool = False,
    ):
        self.location_url = None
        self.slug = slug
        if slug:
            self.location_url = self.URL.format(slug)
        self.categories = categories
        self.soup = None
        self.save_fetched_data = save_fetched_data
        super().__init__()

    def fetch_data(self) -> str:
        if not self.location_url:
            raise ValueError('You must configure the location URL')
        response = requests.get(self.location_url, headers=self.REQUEST_HEADERS)
        response.raise_for_status()
        if self.save_fetched_data:
            with open(
                os.path.join(
                    self.DUMP_STORAGE_PATH, f'{self.slug}.html',
                ),
                'w',
            ) as outfile:
                outfile.write(response.text)
        return response.text

    def parse_html(self, data: str) -> List[BeerData]:
        self.soup = BeautifulSoup(data, 'lxml')
        # the last updated time is only a date
        # it's in a <span> in the form "Updated: M/D/YYYY"
        updated_span = self.soup.find_all(
            lambda tag: (
                tag.name == 'span' and
                not tag.attrs and
                tag.text.startswith('Updated:')
            )
        )[0]
        # they just give us a date. I'm going to arbitrarily declare that to be
        # midnight UTC because who cares if we're off by a day
        updated_date = UTC.localize(parse(
            updated_span.text.split()[1], dayfirst=False,
        ))
        # TODO save this to the venue
        LOG.debug('Last updated: %s', updated_date)

        # the beer lists are in <ul>s
        beers = []
        uls = self.soup.find_all('ul')
        for tag in uls:
            tag_id = tag.attrs.get('id')
            if not tag_id:
                continue
            if self.categories and tag_id not in self.categories:
                LOG.debug("Skipping beer list %s", tag_id)
                continue
            # yay we got a list
            LOG.debug('Processing list %s', tag_id)
            for li in tag.find_all('li'):
                load_more = li.find_all('a', class_='on_tap')
                if load_more:
                    LOG.debug('found view more link')
                    # we have a view all on tap link
                    load_more_url = load_more[0].attrs['href']
                    # this load more link fetches a jQuery call to modify
                    # the DOM and insert the extra <li> tags with the beer
                    # data
                    # No, it doesn't fetch the raw data and then plug it into
                    # a jQuery call; it literally fetches the JS and executes
                    # it.
                    # TODO if we ever get a venue with >40 taps in one category:
                    # check whether we have to load more *again* (I know..)
                    resp = requests.get(
                        f'https://www.beermenus.com{load_more_url}',
                        headers=self.XHR_HEADERS,
                    )
                    resp.raise_for_status()
                    jq_call = resp.text.strip()
                    if self.save_fetched_data:
                        with open(
                            os.path.join(
                                self.DUMP_STORAGE_PATH,
                                f'{load_more_url.replace("?", "__").split("/")[-1]}.js',
                            ),
                            'w',
                        ) as outfile:
                            outfile.write(jq_call)
                    trailing = (
                        '").appendTo("#on_tap");\n$'
                        '(".pure-list-item-more.is-loading"'
                        ').removeClass("is-loading").hide();'
                    )
                    if not jq_call.startswith('$("') or not jq_call.endswith(
                        trailing
                    ):
                        raise ValueError(
                            f'Got unexpected response loading more '
                            f'(https://www.beermenus.com{load_more_url}):'
                            f' {jq_call[:100]}'
                        )
                    # undo the escaping
                    html = jq_call[3:0 - len(trailing)].replace(
                        '\\n', '\n'
                    ).replace('\\/', '/').replace('\\"', '"')
                    parser = BeautifulSoup(html, 'lxml')
                    beers += [
                        parse_beer_tag(extra_tag)
                        for extra_tag in parser.find_all('li')
                    ]
                    continue

                beers.append(
                    parse_beer_tag(li)
                )
        LOG.debug('Found %s beers', len(beers))
        return beers

    def parse_beers(self, beers: List[BeerData]) -> None:
        # we have a list of BeerData instances
        # modify them in place to get the other data
        for beer in beers:
            resp = requests.get(
                beer.url,
                headers=self.REQUEST_HEADERS,
            )
            resp.raise_for_status()
            if self.save_fetched_data:
                with open(
                    os.path.join(
                        self.DUMP_STORAGE_PATH, f'{beer.url.split("/")[-1]}.html',
                    ),
                    'w',
                ) as outfile:
                    outfile.write(resp.text)
            parser = BeautifulSoup(resp.text, 'lxml')
            target_div = parser.find_all('div', class_='splash-small')[0]
            beer_info = target_div.find_all('p', class_='mb-tiny')[0]
            try:
                style, abv_raw, _ = [i.strip() for i in beer_info.text.split(MIDDOT)]
            except ValueError:
                LOG.error(
                    'Unable to parse info for %s: %r (%s)',
                    beer.name,
                    beer_info.text,
                    [ord(i) for i in beer_info.text],
                )
                raise
            abv = Decimal(abv_raw.split('%')[0])
            beer.abv = abv
            beer.style = style
            brewery_p = target_div.find_all('p', class_='mb-0')[0]
            brewery_a = brewery_p.find_all('a')[0]
            beer.brewery_slug = brewery_a.attrs['href'].split('/')[-1]
            beer.brewery_name = brewery_a.text
            beer.brewery_location = brewery_p.text.split(MIDDOT)[1].strip()

    def handle_venue(self, venue: Venue) -> None:
        self.categories = venue.api_configuration.beermenus_categories
        self.location_url = self.URL.format(venue.api_configuration.beermenus_slug)
        data = self.fetch_data()
        beers = self.parse_html(data)
        self.parse_beers(beers)
        LOG.info('Found %s taps from %s', len(beers), venue)
        existing_taps = {
            tap.tap_number: tap for tap in venue.taps.all()
        }
        # delete unused taps
        Tap.objects.filter(venue=venue, tap_number__gt=len(beers)).delete()

        for index, beer in enumerate(beers):
            tap_number = index + 1
            tap = existing_taps.get(
                tap_number,
                Tap(venue=venue, tap_number=tap_number)
            )
            manufacturer = self.get_manufacturer(
                name=beer.brewery_name,
                location=beer.brewery_location,
                beermenus_slug=beer.brewery_slug.split('/')[-1],
            )
            beer = self.get_beer(
                name=beer.name,
                style=beer.style,
                venue=venue,
                pricing=[{
                    'volume_oz': beer.serving_size,
                    'price': beer.price,
                }],
                abv=beer.abv,
                beermenus_slug=beer.url.split('/')[-1],
                manufacturer=manufacturer,
            )
            if not tap.id or tap.beer_id != beer.id:
                tap.beer = beer
                LOG.debug('Saving %s to tap number %s', beer, tap_number)
                tap.save()
            else:
                LOG.debug(
                    'Not updating tap %s because it is already assigned to %s',
                    tap_number, beer,
                )


def parse_beer_tag(tag: Tag) -> BeerData:
    try:
        price_p = tag.find_all('p', class_='caption text-right mb-0')[0]
        capacity, price = [i.strip() for i in price_p.text.split('$')]
    except IndexError:
        LOG.warning('Missing price info for %s', tag)
        price = None
        serving_size = None
    else:
        price = Decimal(price)
        serving_size = int(''.join(i for i in capacity if i.isdigit()))
    beer_a = tag.find_all('a')[0]
    beer_url = f"https://www.beermenus.com{beer_a.attrs['href']}"
    return BeerData(
        url=beer_url,
        price=price,
        serving_size=serving_size,
        style=None,
        brewery_location=None,
        brewery_name=None,
        abv=None,
        brewery_slug=None,
        name=beer_a.text.strip(),
    )


if __name__ == '__main__':
    import argparse

    LOCATIONS = {
        'baddaddy': {
            'slug': '64594-bad-daddy-s-burger-bar-huntsville',
            'categories': ['on_tap', 'featured'],
        },
        'beau': {
            'slug': '52478-beauregard-s',
            'categories': ['craft_beer', 'domestic_draft', 'local'],
        },
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('--dump', action='store_true')
    parser.add_argument('location')
    args = parser.parse_args()

    t = BeerMenusParser(
        save_fetched_data=args.dump,
        **LOCATIONS[args.location],
    )
    data = t.fetch_data()

    beers = t.parse_html(data)
    t.parse_beers(beers)

    for beer in beers:
        print(f'{beer.name} by {beer.brewery_name} ({beer.abv}%, {beer.style})')
