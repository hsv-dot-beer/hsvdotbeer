"""Test the parsing of Arryved embedded menu data"""
import os
import json
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
import responses

from hsv_dot_beer.config.local import BASE_DIR
from beers.models import Beer, Manufacturer
from beers.test.factories import ManufacturerFactory
from venues.test.factories import VenueFactory
from venues.models import VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.parsers.arryved_menu import ArryvedMenuParser


class CommandsTestCase(TestCase):
    fixtures = ["serving_sizes"]

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.manufacturer = ManufacturerFactory()
        cls.venue = VenueFactory(tap_list_provider=ArryvedMenuParser.provider_name)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue,
            arryved_location_id="abc123",
            arryved_menu_id="def456",
            arryved_manufacturer_name=cls.manufacturer.name,
            arryved_serving_sizes=[
                "TAS",
                "32O",
                "64O",
                "13O",
                "PIN",
            ],
        )
        with open(
            os.path.join(
                os.path.dirname(BASE_DIR),
                "tap_list_providers",
                "example_data",
                "arryved_menu.json",
            ),
            "rb",
        ) as json_file:
            cls.json_data = json.loads(json_file.read())

    @responses.activate
    def test_parsing(self):
        responses.add(
            responses.POST,
            ArryvedMenuParser.URL,
            json=self.json_data,
            status=200,
        )
        for dummy in range(2):
            # running twice to make sure we're not double-creating
            args = []
            opts = {}
            call_command("parsearryvedmenu", *args, **opts)
            self.assertEqual(Manufacturer.objects.count(), 1)
            self.assertEqual(Tap.objects.count(), 16)
            self.assertEqual(Beer.objects.count(), 16)
            for tap in Tap.objects.all():
                self.assertEqual(tap.time_updated.year, 2020)
            tap = Tap.objects.select_related("beer").get(tap_number=2)
            self.assertEqual(tap.beer.name, "Charmer Tropical IPA")
            expected_prices = {
                Decimal(6): Decimal(3),
                Decimal(16): Decimal(6),
            }
            prices = tap.beer.prices.select_related("serving_size")
            actual_prices = {
                price.serving_size.volume_oz: price.price for price in prices
            }
            self.assertEqual(expected_prices, actual_prices)
