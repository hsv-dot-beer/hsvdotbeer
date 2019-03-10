"""Test the parsing of stem and stein data"""
import os

from django.core.management import call_command
from django.test import TestCase
import responses

from beers.models import Beer, Manufacturer
from venues.test.factories import VenueFactory
from venues.models import Venue, VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.parsers.stemandstein import StemAndSteinParser
from hsv_dot_beer.config.local import BASE_DIR


class CommandsTestCase(TestCase):

    fixtures = ['example_style_data', 'serving_sizes']

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
                venue=self.venue, tap_number__in=[1, 17],
            ).select_related(
                'beer__style',
            ).order_by('tap_number')
            tap = taps[0]
            self.assertTrue(
                tap.beer.name.endswith('Space Blood Orange Cider'),
                tap.beer.name,
            )
            prices = list(tap.beer.prices.all())
            self.assertEqual(len(prices), 1)
            price = prices[0]
            self.assertEqual(price.price, 5)
            self.assertEqual(price.serving_size.volume_oz, 16)
            tap = taps[1]
            # this one ends with an asterisk. Make sure it's stripped.
            self.assertTrue(
                tap.beer.name.endswith('Karmeliet'),
                tap.beer.name,
            )
            prices = list(tap.beer.prices.all())
            self.assertEqual(len(prices), 1)
            price = prices[0]
            self.assertEqual(price.price, 8)
            self.assertEqual(price.serving_size.volume_oz, 10)
