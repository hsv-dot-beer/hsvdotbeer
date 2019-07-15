"""Test the parsing of taphunter data"""
import os

from django.core.management import call_command
from django.test import TestCase
import responses

from beers.models import Beer, Manufacturer
from venues.test.factories import VenueFactory
from venues.models import Venue, VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.parsers.taphunter import TaphunterParser
from hsv_dot_beer.config.local import BASE_DIR


class CommandsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory(
            tap_list_provider=TaphunterParser.provider_name)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue, url='https://localhost:8000',
            taphunter_location=12345,
            taphunter_excluded_lists=['Kegs to Go'],
        )
        with open(os.path.join(
            os.path.dirname(BASE_DIR),
            'tap_list_providers',
            'example_data',
            'wagon_wheel.json',
        ), 'rb') as json_file:
            cls.json_data = json_file.read()

    @responses.activate
    def test_exclude_wagon_wheel_kegs(self):
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
            # there are 31 beers in the growler list and 8 in the keg list
            self.assertEqual(Beer.objects.count(), 31)
            # all the rest of the tests are handled by test_taphunter.py
            # no need to repeat them here unless we run into something
            # WW-specific
