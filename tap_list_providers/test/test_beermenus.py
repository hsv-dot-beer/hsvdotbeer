"""Test the parsing of beermenus.com data"""
import os
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
import responses

from beers.models import Beer, Manufacturer, ManufacturerAlternateName
from beers.test.factories import ManufacturerFactory
from venues.test.factories import VenueFactory
from venues.models import Venue, VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.parsers.beermenus import BeerMenusParser


PATH = os.path.join(
    'tap_list_providers',
    'example_data',
    'beermenus',
)


BAD_DADDYS_SLUG = '64594-bad-daddy-s-burger-bar-huntsville'


class CommandsTestCase(TestCase):

    fixtures = ['serving_sizes']

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory(
            tap_list_provider=BeerMenusParser.provider_name)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue,
            beermenus_slug=BAD_DADDYS_SLUG,
            beermenus_categories=['on_tap', 'featured'],
        )
        cls.locations = []
        cls.main_menu = ''
        cls.read_more = ''
        for name in os.listdir(PATH):
            if name.startswith(BAD_DADDYS_SLUG):
                url = (
                    f'https://www.beermenus.com/places/'
                    f'{name.replace("__", "?").split(".")[0]}'
                )
                with open(os.path.join(PATH, name)) as infile:
                    html = infile.read()
                if '?' in url:
                    cls.read_more = html
                else:
                    cls.base_url = url
                    cls.main_menu = html
            else:
                url = (
                    'https://www.beermenus.com/beers/'
                    f'{name.split(".")[0]}'
                )
                with open(os.path.join(PATH, name)) as infile:
                    cls.locations.append((url, name, infile.read()))
        rocket = ManufacturerFactory(name='Rocket Republic Brewing Company')
        ManufacturerAlternateName.objects.create(
            name='Rocket Republic', manufacturer=rocket,
        )

    def beer_menu_callback(self, request):
        if request.url.endswith('?section_id=12'):
            return 200, {}, self.read_more
        return 200, {}, self.main_menu

    @responses.activate
    def test_import_beermenus_data(self):
        """Test parsing the HTML and JS data"""
        for url, name, html in self.locations:
            responses.add(
                responses.GET,
                url,
                body=html,
                status=200,
                headers={'encoding': 'utf-8'},
            )
        responses.add_callback(
            responses.GET,
            self.base_url,
            callback=self.beer_menu_callback,
        )
        self.assertFalse(Tap.objects.exists())
        self.assertEqual(Venue.objects.count(), 1)
        self.assertFalse(Beer.objects.exists())
        deleted_tap = Tap.objects.create(
            venue=self.venue,
            tap_number=3000,
        )
        for dummy in range(2):
            # running twice to make sure we're not double-creating
            args = []
            opts = {}
            call_command('parsebeermenus', *args, **opts)

            self.assertEqual(Beer.objects.count(), 24)
            # three beers from Breckenridge, so only 22 manufacturers
            self.assertEqual(Manufacturer.objects.count(), 22)
            self.assertEqual(Tap.objects.count(), 24)
            taps = Tap.objects.filter(
                venue=self.venue, tap_number__in=[1, 17, 2, 19],
            ).select_related(
                'beer__style', 'beer__manufacturer',
            ).order_by('tap_number')
            tap = taps[0]
            self.assertEqual(
                tap.beer.name.casefold(),
                'bad daddys amber ale',
                tap.beer.name,
            )
            self.assertEqual(tap.beer.manufacturer.location, 'Littleton, CO')
            self.assertEqual(tap.beer.abv, Decimal('5.0'))
            self.assertEqual(tap.beer.style.name, 'Amber Ale')
            prices = list(tap.beer.prices.all())
            self.assertEqual(len(prices), 1)
            price = prices[0]
            self.assertEqual(price.price, 4)
            self.assertEqual(price.serving_size.volume_oz, 16)

            tap = taps[1]
            self.assertEqual(tap.beer.name, 'Crisp Apple Cider')
            self.assertEqual(tap.beer.manufacturer.name, 'Angry Orchard')

            tap = taps[2]
            self.assertEqual(
                tap.beer.name,
                'Modelo Especial',
                tap.beer.name,
            )
            # due to a bug in responses, we can't validate the location
            # (it doesn't handle the special chars properly)
            prices = list(tap.beer.prices.all())
            self.assertEqual(len(prices), 1)
            price = prices[0]
            self.assertEqual(price.price, 6)
            self.assertEqual(price.serving_size.volume_oz, 16)
            self.assertFalse(Tap.objects.filter(id=deleted_tap.id).exists())

            tap = taps[3]
            self.assertEqual(tap.beer.name, 'Vapor Trail Cream Ale')
            self.assertEqual(
                tap.beer.manufacturer.name, 'Rocket Republic Brewing Company',
            )
