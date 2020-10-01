"""Test the parsing of untappd data"""
import os
from decimal import Decimal
from unittest import mock

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
        cls.venue = VenueFactory(tap_list_provider=UntappdParser.provider_name)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue,
            url="https://localhost:8000",
            untappd_location=3884,
            untappd_theme=11913,
            untappd_categories=["Tap List"],
        )
        with open(
            os.path.join(
                os.path.dirname(BASE_DIR),
                "tap_list_providers",
                "example_data",
                "dsb-stray-backslash.js",
            ),
            "rb",
        ) as js_file:
            cls.js_data = js_file.read()

    @responses.activate
    @mock.patch("tap_list_providers.base.look_up_beer")
    def test_import_untappd_data(self, mock_beer_lookup):
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
            call_command("parseuntappd", *args, **opts)

            self.assertEqual(Beer.objects.count(), 32)
            self.assertEqual(Manufacturer.objects.count(), 28)
            self.assertEqual(Tap.objects.count(), 32)
            tap = (
                Tap.objects.filter(
                    venue=self.venue,
                    tap_number=21,
                )
                .select_related(
                    "beer__style",
                )
                .get()
            )
            self.assertEqual(tap.beer.name, "Delirium Tremens")
            self.assertEqual(tap.beer.abv, Decimal("8.5"))

            prices = {
                Decimal(64): Decimal(49),  # $49 for a growler... daaaaaamn
                Decimal(32): Decimal(25),
                Decimal(10): Decimal(9.25),
                Decimal(4): Decimal(4.25),
            }
            price_instances = list(
                tap.beer.prices.select_related("serving_size", "venue")
            )
            self.assertEqual(
                len(price_instances),
                len(prices),
                price_instances,
            )
            for price_instance in price_instances:
                self.assertEqual(price_instance.venue, self.venue, price_instance)
                self.assertIn(
                    price_instance.serving_size.volume_oz, prices, price_instance
                )
                self.assertEqual(
                    prices[price_instance.serving_size.volume_oz],
                    price_instance.price,
                    price_instance,
                )
            mock_beer_lookup.delay.assert_called()
