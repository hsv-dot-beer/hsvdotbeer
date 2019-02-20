"""Test the parsing of untappd data"""
import os
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
import responses

from beers.models import Beer, Manufacturer
from venues.test.factories import VenueFactory
from venues.models import Venue, VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.parsers.untappd import UntappdParser
from hsv_dot_beer.config.local import BASE_DIR


class CommandsTestCase(TestCase):

    fixtures = ['example_style_data']

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory(
            tap_list_provider=UntappdParser.provider_name)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue, url='https://localhost:8000',
            untappd_location=12345,
            untappd_theme=55242,
            untappd_categories=['YEAR-ROUND', 'SEASONALS', 'Beer'],
        )
        with open(os.path.join(
            os.path.dirname(BASE_DIR),
            'tap_list_providers',
            'example_data',
            'yellowhammer.js',
        ), 'rb') as js_file:
            cls.js_data = js_file.read()

    @responses.activate
    def test_import_data(self):
        """Test parsing the JSON data"""
        responses.add(
            responses.GET,
            UntappdParser.URL.format(
                self.venue_cfg.untappd_location,
                self.venue_cfg.untappd_theme,
            ),
            body=self.js_data,
            status=200,
        )
        self.assertFalse(Tap.objects.exists())
        self.assertEqual(Venue.objects.count(), 1)
        self.assertFalse(Beer.objects.exists())
        self.assertFalse(Manufacturer.objects.exists())
        for dummy in range(2):
            # running twice to make sure we're not double-creating
            args = []
            opts = {}
            call_command('parseuntappd', *args, **opts)

            self.assertEqual(Beer.objects.count(), 22)
            self.assertEqual(Manufacturer.objects.count(), 1)
            self.assertEqual(Tap.objects.count(), 22)
            tap = Tap.objects.filter(
                venue=self.venue, tap_number=22,
            ).select_related(
                'beer__style',
            ).get()
            self.assertEqual(tap.beer.name, "Tobacco Road")
            self.assertEqual(tap.beer.abv, Decimal('9.4'))
            self.assertIsNone(tap.beer.style)
            self.assertEqual(tap.gas_type, '')
            self.assertEqual(
                tap.beer.api_vendor_style, 'Red Ale - Imperial / Double')
            self.assertEqual(
                tap.beer.untappd_url,
                'https://untappd.com/b/yellowhammer-brewing-tobacco-road/32727',
            )
            self.assertEqual(
                tap.beer.manufacturer.untappd_url,
                'https://untappd.com/brewery/8036',
            )
            self.assertEqual(
                tap.beer.logo_url,
                'https://untappd.akamaized.net/site/beer_logos/'
                'beer-_32727_63923de6f1587043d09e3a967cce.jpeg',
            )
