"""Test the parsing of untappd data"""
import os
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


class GoatIslandTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory(
            tap_list_provider=UntappdParser.provider_name,
            name="Goat Island Brewing",
        )
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue,
            url="https://localhost:8000",
            untappd_location=4632,
            untappd_theme=14806,
            untappd_categories=["Goat Island Brewing"],
        )
        with open(
            os.path.join(
                os.path.dirname(BASE_DIR),
                "tap_list_providers",
                "example_data",
                "goat-no-brewery.html",
            ),
            "rb",
        ) as js_file:
            cls.js_data = js_file.read()

    @responses.activate
    @mock.patch("tap_list_providers.base.look_up_beer")
    def test_import_untappd_data(self, _):
        """Test parsing the HTML data"""
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
        for _ in range(2):
            # running twice to make sure we're not double-creating
            args = []
            opts = {}
            call_command("parseuntappd", *args, **opts)

            self.assertTrue(Beer.objects.exists())
            self.assertEqual(Manufacturer.objects.count(), 1)
            self.assertEqual(Beer.objects.count(), 12)
            beer: Beer = Beer.objects.filter(name__icontains="Dinkleberg").get()
            self.assertTrue(beer.prices.exists())
            self.assertTrue(
                Manufacturer.objects.filter(name="Goat Island").exists(),
                Manufacturer.objects.all(),
            )
