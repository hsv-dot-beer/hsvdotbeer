"""Test the parsing of digitalpour data"""
import json
import os

from django.core.management import call_command
from django.test import TestCase
from django.utils.timezone import now
import responses

from beers.models import Beer, Manufacturer
from venues.test.factories import VenueFactory
from venues.models import Venue, VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.parsers.digitalpour import DigitalPourParser
from hsv_dot_beer.config.local import BASE_DIR


class CommandsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory(tap_list_provider=DigitalPourParser.provider_name)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue,
            url="https://localhost:8000",
            digital_pour_venue_id=12345,
            digital_pour_location_number=1,
        )
        with open(
            os.path.join(
                os.path.dirname(BASE_DIR),
                "tap_list_providers",
                "example_data",
                "madison-taproom.json",
            ),
            "rb",
        ) as json_file:
            cls.json_data = json.loads(json_file.read())

    @responses.activate
    def test_import_digitalpour_data(self):
        """Test parsing the JSON data"""
        timestamp = now()
        responses.add(
            responses.GET,
            DigitalPourParser.URL.format(
                self.venue_cfg.digital_pour_venue_id,
                self.venue_cfg.digital_pour_location_number,
                DigitalPourParser.APIKEY,
            ),
            json=self.json_data,
            status=200,
        )
        self.assertFalse(Tap.objects.exists())
        self.assertEqual(Venue.objects.count(), 1)
        self.assertFalse(Beer.objects.exists())
        self.assertFalse(Manufacturer.objects.exists())
        for _ in range(2):
            # running twice to make sure we're not double-creating
            args = []
            opts = {}
            call_command("parsedigitalpour", *args, **opts)

            self.assertEqual(Beer.objects.count(), 22, list(Beer.objects.all()))
            self.assertEqual(Manufacturer.objects.count(), 20)
            self.assertEqual(Tap.objects.count(), 22)
            tap = Tap.objects.select_related("beer__style", "beer__manufacturer").get(
                venue=self.venue, tap_number=11
            )
            self.assertEqual(tap.beer.name, "Two Hearted Ale")
            self.assertEqual(tap.beer.manufacturer.name, "Bell's")

        self.venue.refresh_from_db()
        self.assertIsNotNone(self.venue.tap_list_last_check_time)
        self.assertGreater(self.venue.tap_list_last_check_time, timestamp)
        self.assertIsNotNone(self.venue.tap_list_last_update_time)
