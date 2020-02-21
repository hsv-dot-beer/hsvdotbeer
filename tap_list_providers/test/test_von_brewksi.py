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

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory(
            tap_list_provider=UntappdParser.provider_name)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue, url='https://localhost:8000',
            untappd_location=12345,
            untappd_theme=55242,
            untappd_categories=['Left Wall', 'Back Wall', 'Right Wall', 'Trailer', 'On Deck'],
        )
        with open(os.path.join(
            os.path.dirname(BASE_DIR),
            'tap_list_providers',
            'example_data',
            'von_brewski.js',
        ), 'rb') as js_file:
            cls.js_data = js_file.read()

    @responses.activate
    def test_import_untappd_data(self):
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

            self.assertEqual(Beer.objects.count(), 177)
            self.assertEqual(Manufacturer.objects.count(), 63)
            self.assertEqual(Tap.objects.count(), 177)
            tap = Tap.objects.filter(
                venue=self.venue, tap_number=21,
            ).select_related(
                'beer__style',
            ).get()
            self.assertEqual(tap.beer.name, "30A Beach Blonde Ale")
            self.assertEqual(tap.beer.abv, Decimal('4.6'))
            self.assertEqual(tap.beer.ibu, 13)
            self.assertEqual(tap.gas_type, '')
            self.assertEqual(tap.beer.manufacturer.name, 'Grayton')
            # NOTE I can't test for an exact match due to a bug in responses.
            # The real style parsing works though.
            self.assertIn('Blonde Ale', tap.beer.style.name)
            self.assertIsNone(tap.beer.untappd_url)
            self.assertIsNone(tap.beer.manufacturer.untappd_url)
            self.assertIsNone(tap.beer.logo_url)
            self.assertFalse(tap.beer.prices.exists())
