"""Test the parsing of taphunter data"""
import os
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
import responses

from beers.models import Beer, Manufacturer
from venues.test.factories import VenueFactory, RoomFactory
from venues.models import Venue, VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.parsers.taphunter import TaphunterParser
from hsv_dot_beer.config.local import BASE_DIR


class CommandsTestCase(TestCase):

    fixtures = ['example_style_data']

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory(
            tap_list_provider=TaphunterParser.provider_name)
        cls.room = RoomFactory(venue=cls.venue)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue, url='https://localhost:8000',
            taphunter_location=12345,
        )
        with open(os.path.join(
            os.path.dirname(BASE_DIR),
            'tap_list_providers',
            'example_data',
            'liquor_express.json',
        ), 'rb') as json_file:
            cls.json_data = json_file.read()

    @responses.activate
    def test_import_data(self):
        """Test parsing the JSON data"""
        responses.add(
            responses.GET,
            TaphunterParser.URL.format(
                self.venue_cfg.taphunter_location
            ),
            body=self.json_data,
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
            call_command('parsetaphunter', *args, **opts)

            self.assertEqual(Beer.objects.count(), 93)
            self.assertEqual(Manufacturer.objects.count(), 52)
            self.assertEqual(Tap.objects.count(), 93)
            tap = Tap.objects.filter(
                room=self.room, tap_number=22,
            ).select_related(
                'beer__style',
            ).get()
            self.assertEqual(tap.beer.name, "Something Cold")
            self.assertEqual(tap.beer.abv, Decimal('5.00'))
            self.assertIsNone(tap.beer.style)
            self.assertEqual(tap.gas_type, '')
