"""Test the parsing of digitalpour data"""
import json
import os

from django.core.management import call_command
from django.test import TestCase
import responses

from beers.models import Beer, Manufacturer
from venues.test.factories import VenueFactory
from venues.models import Venue, VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.parsers.digitalpour import DigitalPourParser
from hsv_dot_beer.config.local import BASE_DIR


class OTBXTestCase(TestCase):
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
                "otbx-duplicate-tap-13.json",
            ),
            "rb",
        ) as json_file:
            cls.json_data = json.loads(json_file.read())

    @responses.activate
    def test_import_digitalpour_data(self):
        """Test parsing the JSON data"""
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

            # tap 2 is vacant and tap 13 is double-assigned
            self.assertEqual(
                list(
                    Tap.objects.order_by("tap_number").values_list(
                        "tap_number",
                        flat=True,
                    )
                ),
                [1] + list(range(3, 33)),
            )
            self.assertEqual(Tap.objects.count(), 31)
            self.assertEqual(
                Beer.objects.count(),
                30,  # snake handler is listed twice
                list(
                    Beer.objects.order_by("taps__tap_number"),
                ),
            )
            self.assertEqual(Manufacturer.objects.count(), 25)
