"""Test the parsing of taplist.io data"""
import json
import os

from dateutil.parser import parse
from django.core.management import call_command
from django.test import TestCase
from django.utils.timezone import now
import responses

from beers.models import Beer, Manufacturer
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
        cls.timestamp = parse("2022-09-13T16:32:29.403362-05:00")
        cls.venue = VenueFactory(tap_list_provider=TaplistDotIOParser.provider_name)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue,
            url="https://localhost:8000",
            taplist_io_access_code="123456",
            taplist_io_display_id="abcdef-abcdef",
        )
        with open(
            os.path.join(
                os.path.dirname(BASE_DIR),
                "tap_list_providers",
                "example_data",
                "taplist_io_v6.json",
            ),
            "rb",
        ) as json_file:
            cls.json_data = json.loads(json_file.read())

    @responses.activate
    def test_import_taplist_io_data(self):
        """Test parsing the JSON data"""
        timestamp = now()
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
            name="InnerSpace",
            alternate_names=[
                "Isb",
                "InnerSpace Brewing  Company",
                "InnerSpace Brewing co",
            ],
        )
        for _ in range(2):
            # running twice to make sure we're not double-creating
            args = []
            opts = {}
            call_command("parsetaplistio", *args, **opts)

            self.assertEqual(Beer.objects.count(), 13, list(Beer.objects.all()))
            # they had a collab with Khonso on tap as of the time I took the snapshot
            self.assertEqual(
                Manufacturer.objects.count(), 2, Manufacturer.objects.all()
            )
            self.assertEqual(Tap.objects.count(), 14)
            taps = (
                Tap.objects.filter(
                    venue=self.venue,
                    tap_number__in=[8, 3, 1],
                )
                .select_related(
                    "beer__style",
                    "beer__manufacturer",
                )
                .order_by("tap_number")
            )
            tap = taps[2]
            # tap #8 is skyfarmer
            self.assertEqual(tap.beer.name, "SkyFarmer Farmhouse Ale")
            self.assertEqual(tap.beer.manufacturer.name, mfg.name)
            self.assertEqual(tap.beer.style.name, "Farmhouse Ale")
            self.assertEqual(tap.time_updated, self.timestamp)
            tap = taps[0]
            # tap #1 is blank
            self.assertIsNone(tap.beer_id)
            self.assertEqual(tap.time_updated, self.timestamp)
            tap = taps[1]
            # tap #3 is ic3pa
            self.assertEqual(tap.beer.manufacturer.name, mfg.name)
            self.assertEqual(tap.beer.name, "IC3PA")
            self.assertEqual(tap.beer.style.name, "India Pale Ale")
            self.assertEqual(tap.time_updated, self.timestamp)
        self.venue.refresh_from_db()
        self.assertIsNotNone(self.venue.tap_list_last_check_time)
        self.assertGreater(self.venue.tap_list_last_check_time, timestamp)
        self.assertIsNotNone(self.venue.tap_list_last_update_time)
