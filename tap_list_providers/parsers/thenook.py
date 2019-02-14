"""HTML scraper for The Nook"""
from decimal import Decimal
import os

from bs4 import BeautifulSoup
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

from beers.models import Manufacturer
from taps.models import Tap


class NookParser(BaseTapListProvider):
    """Parser for The Nook's static HTML page

    Note: because The Nook uses rows inside of columns instead of the more
    common reverse, we essentially have to look up the components we need
    separately and then zip() them together.
    """

    provider_name = 'nook_html'

    NAME_COLUMN_ID = 'id9'
    # TODO (#37): parse styles
    STYLE_COLUMN_ID = 'id10'
    BREWERY_COLUMN_ID = 'id12'
    ABV_COLUMN_ID = 'id17'

    def __init__(self):
        self.parser = None
        super().__init__()

    def fetch_html(self, url):
        self.parser = BeautifulSoup(requests.get(url).content, 'html.parser')

    def dump_html(self):
        print(self.parser.prettify())

    def get_names(self):
        return list(
            i.contents[0].replace('*', '').strip() for i in
            self.parser.find(id=self.NAME_COLUMN_ID).find_all('p')
        )

    def get_abvs(self):
        return list(
            Decimal(i.contents[0].strip())
            # weirdly, the ABVs are in spans
            for i in self.parser.find(id=self.ABV_COLUMN_ID).find_all('span')
        )

    def get_manufacturers(self):
        return list(
            i.contents[0] for i in
            self.parser.find(id=self.BREWERY_COLUMN_ID).find_all('p')
        )

    def get_styles(self):
        return list(
            i.contents[0].strip()
            for i in self.parser.find(id=self.STYLE_COLUMN_ID).find_all('p')
        )

    def venue_details(self):
        return enumerate(zip(
            self.get_names(), self.get_manufacturers(), self.get_abvs(),
            self.get_styles(),
        ))

    def handle_venue(self, venue):
        url = venue.api_configuration.url
        self.fetch_html(url)
        rooms = list(venue.rooms.all())
        if not rooms:
            raise ValueError(f'You must create a room for {venue} first.')
        if len(rooms) != 1:
            raise ValueError(
                f'DigitalPour does not support rooms! {len(rooms)} found',
            )
        room = rooms[0]
        taps = {tap.tap_number: tap for tap in room.taps.all()}
        manufacturers = {mfg.name: mfg for mfg in Manufacturer.objects.filter(
            name__in=self.get_manufacturers()
        )}
        for index, (name, mfg, abv, style) in self.venue_details():
            tap_number = index + 1
            # 1. get the tap
            try:
                tap = taps[tap_number]
            except KeyError:
                tap = Tap(room=room, tap_number=tap_number)
            # 2. get the mfg
            try:
                manufacturer = manufacturers[mfg]
            except KeyError:
                manufacturer = Manufacturer.objects.get_or_create(
                    name=mfg,
                )[0]
                manufacturers[manufacturer.name] = manufacturer
            # 3. get the beer
            beer = self.get_beer(
                name, manufacturer, abv=abv, api_vendor_style=style,
            )
            if tap.beer_id != beer.id:
                tap.beer = beer
                # only save if beer changed so as not to disturb updated time
                tap.save()
