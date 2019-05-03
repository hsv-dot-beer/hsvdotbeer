"""Test the parsing of taplist.io data"""
import json
import os

from dateutil.parser import parse
from django.core.management import call_command
from django.test import TestCase
import responses

from beers.models import Beer, Manufacturer, ManufacturerAlternateName
from beers.test.factories import ManufacturerFactory
from venues.test.factories import VenueFactory
from venues.models import Venue, VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.parsers.taplist_io import TaplistDotIOParser
from hsv_dot_beer.config.local import BASE_DIR


class TaplistCommandsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.timestamp = parse("2019-05-01T19:51:12.344272Z")
        cls.venue = VenueFactory(
            tap_list_provider=TaplistDotIOParser.provider_name)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue, url='https://localhost:8000',
            taplist_io_access_code='123456',
            taplist_io_display_id='abcdef-abcdef',
        )
        with open(os.path.join(
            os.path.dirname(BASE_DIR),
            'tap_list_providers',
            'example_data',
            'innerspace.json',
        ), 'rb') as json_file:
            cls.json_data = json.loads(json_file.read())

    @responses.activate
    def test_import_taplist_io_data(self):
        """Test parsing the JSON data"""
        responses.add(
            responses.GET,
            TaplistDotIOParser.URL.format(
                self.venue_cfg.taplist_io_display_id,
            ),
            json=self.json_data,
            status=200,
        )
        self.assertFalse(Tap.objects.exists())
        self.assertEqual(Venue.objects.count(), 1)
        self.assertFalse(Beer.objects.exists())
        self.assertFalse(Manufacturer.objects.exists())
        mfg = ManufacturerFactory(
            name='InnerSpace',
        )
        ManufacturerAlternateName.objects.bulk_create(
            ManufacturerAlternateName(
                manufacturer=mfg,
                name=name,
            )
            for name in [
                'Isb', 'InnerSpace Brewing  Company', 'InnerSpace Brewing co',
            ]
        )
        for dummy in range(2):
            # running twice to make sure we're not double-creating
            args = []
            opts = {}
            call_command('parsetaplistio', *args, **opts)

            self.assertEqual(Beer.objects.count(), 10, list(Beer.objects.all()))
            self.assertEqual(Manufacturer.objects.count(), 1)
            self.assertEqual(Tap.objects.count(), 13)
            taps = Tap.objects.filter(
                venue=self.venue, tap_number__in=[1, 2, 10],
            ).select_related(
                'beer__style', 'beer__manufacturer',
            ).order_by('tap_number')
            tap = taps[0]
            self.assertEqual(tap.beer.name, 'SkyFarmer Farmhouse Ale')
            self.assertEqual(tap.beer.manufacturer.name, mfg.name)
            self.assertEqual(tap.beer.style.name, "Farmhouse Ale")
            self.assertEqual(tap.time_updated, self.timestamp)
            # location nulled out in test data
            tap = taps[1]
            self.assertIsNone(tap.beer_id)
            self.assertEqual(tap.time_updated, self.timestamp)
            tap = taps[2]
            self.assertEqual(tap.beer.manufacturer.name, mfg.name)
            self.assertEqual(tap.beer.name, 'Denver Destroyer')
            # NOTE: Yes, really.
            self.assertEqual(tap.beer.style.name, 'An elusive IPA')
            self.assertEqual(tap.time_updated, self.timestamp)
