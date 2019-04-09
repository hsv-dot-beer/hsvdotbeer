"""Test the parsing of thenook data"""
import os
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
import responses

from beers.models import Beer, Manufacturer
from venues.test.factories import VenueFactory
from venues.models import Venue, VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.parsers.thenook import NookParser
from hsv_dot_beer.config.local import BASE_DIR


class CommandsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory(
            tap_list_provider=NookParser.provider_name)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue, url='https://localhost:8000',
            digital_pour_venue_id=12345,
            digital_pour_location_number=1,
        )
        with open(os.path.join(
            os.path.dirname(BASE_DIR),
            'tap_list_providers',
            'example_data',
            'the_nook.html',
        ), 'rb') as html_file:
            cls.html_data = html_file.read()

    @responses.activate
    def test_import_nook_data(self):
        """Test parsing the JSON data"""
        responses.add(
            responses.GET,
            'https://localhost:8000',
            body=self.html_data,
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
            call_command('parsethenook', *args, **opts)

            self.assertEqual(Beer.objects.count(), 80)
            self.assertLess(Manufacturer.objects.count(), 80)
            self.assertEqual(Tap.objects.count(), 80)
            taps = Tap.objects.filter(
                venue=self.venue, tap_number__in=[1, 18],
            ).select_related(
                'beer__style',
            ).order_by('tap_number')
            tap = taps[0]
            self.assertEqual(tap.beer.name, 'Angry Orchard Crisp Apple')
            self.assertEqual(tap.beer.abv, Decimal('5.0'))
            self.assertEqual(tap.gas_type, '')
            self.assertEqual(tap.beer.style.name, 'Hard Cider')
            tap = taps[1]
            # this one ends with an asterisk. Make sure it's stripped.
            self.assertEqual(tap.beer.name, 'Delirium Tremens')
