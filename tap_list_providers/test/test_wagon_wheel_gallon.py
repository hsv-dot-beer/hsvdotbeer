"""Test the parsing of wagon wheel data

We just want to ensure that 1 gallon serving sizes get ignored
"""
import os

from django.core.management import call_command
from django.test import TestCase
import responses

from beers.models import Beer, Manufacturer, ServingSize
from venues.test.factories import VenueFactory
from venues.models import Venue, VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.parsers.taphunter import TaphunterParser
from hsv_dot_beer.config.local import BASE_DIR


class WagonWheelTestCase(TestCase):
    fixtures = ["serving_sizes"]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory(tap_list_provider=TaphunterParser.provider_name)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue,
            url="https://localhost:8000",
            taphunter_location=12345,
        )
        with open(
            os.path.join(
                os.path.dirname(BASE_DIR),
                "tap_list_providers",
                "example_data",
                "wagonwheel_1_gal.json",
            ),
            "rb",
        ) as json_file:
            cls.json_data = json_file.read()

    @responses.activate
    def test_import_taphunter_data(self):
        """Test parsing the JSON data"""
        responses.add(
            responses.GET,
            TaphunterParser.URL.format(self.venue_cfg.taphunter_location),
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
            call_command("parsetaphunter", *args, **opts)

            self.assertEqual(Beer.objects.count(), 23)
            self.assertEqual(Manufacturer.objects.count(), 19)
            self.assertEqual(Tap.objects.count(), 24)
            self.assertEqual(
                set(
                    ServingSize.objects.exclude(beer_prices__isnull=True).values_list(
                        "volume_oz", flat=True
                    )
                ),
                {32, 64, 128},
            )
