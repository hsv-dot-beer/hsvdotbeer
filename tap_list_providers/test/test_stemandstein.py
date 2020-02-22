"""Test the parsing of stem and stein data"""
import os
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
import responses

from beers.models import (
    Beer, Manufacturer, ManufacturerAlternateName, Style, StyleAlternateName,
)
from beers.test.factories import ManufacturerFactory, BeerFactory
from venues.test.factories import VenueFactory
from venues.models import Venue, VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.parsers.stemandstein import StemAndSteinParser
from hsv_dot_beer.config.local import BASE_DIR


class CommandsTestCase(TestCase):

    fixtures = ['serving_sizes']

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory(
            tap_list_provider=StemAndSteinParser.provider_name)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue, url='https://localhost:8000',
            digital_pour_venue_id=12345,
            digital_pour_location_number=1,
        )
        Style.objects.create(name='Scotch Ale')
        cls.html_data = {}
        with open(os.path.join(
            os.path.dirname(BASE_DIR),
            'tap_list_providers',
            'example_data',
            'stem_and_stein_main.html',
        ), 'rb') as html_file:
            cls.html_data['root'] = html_file.read()
        for pk in [
            136, 237, 266, 404, 456, 710, 967, 993, 1056, 1065, 1078, 1079,
            1081, 1082, 1083, 1084, 1085,
        ]:
            with open(os.path.join(
                os.path.dirname(BASE_DIR),
                'tap_list_providers',
                'example_data',
                f'{pk}.html',
            ), 'rb') as html_file:
                cls.html_data[pk] = html_file.read()

    @responses.activate
    def test_import_stemandstein_data(self):
        """Test parsing the JSON data"""
        for pk, html_data in self.html_data.items():
            if pk == 'root':
                url = 'https://thestemandstein.com/'
            else:
                url = f'https://thestemandstein.com/Home/BeerDetails/{pk}'
            responses.add(responses.GET, url, body=html_data, status=200)
        self.assertFalse(Tap.objects.exists())
        self.assertEqual(Venue.objects.count(), 1)
        self.assertFalse(Beer.objects.exists())
        self.assertFalse(Manufacturer.objects.exists())
        deleted_tap = Tap.objects.create(
            venue=self.venue,
            tap_number=3000,
        )
        mfg = ManufacturerFactory(name='Founders')
        beer = BeerFactory(name='Dirty Bastard', manufacturer=mfg)
        other = Style.objects.create(name='other')
        # Create a fake shorter style name that the search for fruit ale should
        # ignore
        StyleAlternateName.objects.create(name='t Ale', style=other)
        style = Style.objects.create(name='Fruit Beer')
        StyleAlternateName.objects.create(name='Fruit Ale', style=style)
        for dummy in range(2):
            # running twice to make sure we're not double-creating
            args = []
            opts = {}
            call_command('parsestemandstein', *args, **opts)

            self.assertEqual(Beer.objects.count(), 17)
            # Bell's and Founders have two each
            self.assertEqual(Manufacturer.objects.count(), 15)
            self.assertEqual(Tap.objects.count(), 17)
            taps = Tap.objects.filter(
                venue=self.venue, tap_number__in=[1, 3, 9, 17],
            ).select_related(
                'beer__style', 'beer__manufacturer',
            ).order_by('tap_number')
            tap = taps[0]
            self.assertTrue(
                tap.beer.name.endswith('Space Blood Orange Cider'),
                tap.beer.name,
            )
            self.assertEqual(tap.beer.manufacturer.location, 'Sebastopol, CA')
            self.assertEqual(tap.beer.abv, Decimal('6.9'))
            self.assertEqual(tap.beer.stem_and_stein_pk, 967)
            prices = list(tap.beer.prices.all())
            self.assertEqual(len(prices), 1)
            price = prices[0]
            self.assertEqual(price.price, 5)
            self.assertEqual(price.serving_size.volume_oz, 16)
            tap = taps[3]
            # this one ends with an asterisk. Make sure it's stripped.
            self.assertTrue(
                tap.beer.name.endswith('Karmeliet'),
                tap.beer.name,
            )
            self.assertEqual(tap.beer.manufacturer.location, 'Belgium')
            prices = list(tap.beer.prices.all())
            self.assertEqual(len(prices), 1)
            price = prices[0]
            self.assertEqual(price.price, 8)
            self.assertEqual(price.serving_size.volume_oz, 10)
            self.assertFalse(Tap.objects.filter(id=deleted_tap.id).exists())
            # make sure style stripping works
            tap = taps[2]
            self.assertEqual(tap.beer.style.name, 'Scotch Ale')
            self.assertEqual(tap.beer.name, 'Dirty Bastard')
            self.assertEqual(tap.beer.id, beer.id)
            self.assertEqual(tap.beer.manufacturer_id, mfg.id)
            tap = taps[1]
            # style is set to Fruit Ale but the beer name is preserved
            self.assertEqual(tap.beer.style_id, style.id)
            self.assertTrue(tap.beer.name.endswith('Fruit Ale'))

    def test_guess_manufacturer_good_people(self):
        mfg_names = [
            'Goodwood', 'Good People Brewing Company', 'Good People',
            'Good People Brewing Co.',
        ]
        manufacturers = [
            ManufacturerFactory.build(name=name) for name in mfg_names
        ]
        Manufacturer.objects.bulk_create(manufacturers)
        parser = StemAndSteinParser()
        guessed = parser.guess_manufacturer('Good People IPA')
        self.assertEqual(guessed.name, 'Good People', guessed)
        self.assertIn(guessed, manufacturers)

    def test_guess_manufacturer_stone(self):
        mfg_names = [
            'New Realm Brewing Company / Stone', 'Stone Brewing ', 'Stone',
            'Stone Brewing Co.', 'Stone Brewing',
        ]
        manufacturers = [
            ManufacturerFactory.build(name=name) for name in mfg_names
        ]
        Manufacturer.objects.bulk_create(manufacturers)
        parser = StemAndSteinParser()
        guessed = parser.guess_manufacturer('Stone Enjoy By 04.20.19 IPA')
        self.assertEqual(guessed.name, 'Stone', guessed)
        self.assertIn(guessed, manufacturers)

    def test_guess_manufacturer_goat_island(self):
        mfg_names = [
            'Horny Goat Brewing Company', 'Goat Island Brewing', 'Goat Island',
        ]
        manufacturers = [
            ManufacturerFactory.build(name=name) for name in mfg_names
        ]
        Manufacturer.objects.bulk_create(manufacturers)
        parser = StemAndSteinParser()
        guessed = parser.guess_manufacturer('Goat Island Sipsey River Red Ale')
        self.assertEqual(guessed.name, 'Goat Island', guessed)
        self.assertIn(guessed, manufacturers)

    def test_guess_manufacturer_back_forty(self):
        mfg = ManufacturerFactory(name='Back Forty')
        ManufacturerAlternateName.objects.bulk_create(
            ManufacturerAlternateName(name=name, manufacturer=mfg)
            for name in ['Back Forty', 'Back Forty Beer Co']
        )
        parser = StemAndSteinParser()
        guessed = parser.guess_beer('Back Forty Truck Stop Honey Brown')
        self.assertEqual(guessed.manufacturer, mfg)
