"""Test the parsing of untappd data"""
import os
import datetime
from decimal import Decimal
from unittest import mock
import zoneinfo

from django.core.management import call_command
from django.test import TestCase
from django.utils.timezone import now
import responses

from beers.models import Beer, Manufacturer
from beers.test.factories import StyleFactory
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
            untappd_location=12345,
            untappd_theme=55242,
            untappd_categories=["YEAR-ROUND", "SEASONALS", "Beer"],
        )
        with open(
            os.path.join(
                os.path.dirname(BASE_DIR),
                "tap_list_providers",
                "example_data",
                "yellowhammer.js",
            ),
            "rb",
        ) as js_file:
            cls.js_data = js_file.read()

    @responses.activate
    @mock.patch("tap_list_providers.base.look_up_beer")
    def test_import_untappd_data(self, mock_beer_lookup):
        """Test parsing the HTML data"""
        timestamp = now()
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

            self.assertEqual(Beer.objects.count(), 19)
            self.assertEqual(Manufacturer.objects.count(), 1)
            self.assertEqual(Tap.objects.count(), 19)
            tap = (
                Tap.objects.filter(
                    venue=self.venue,
                    tap_number=19,
                )
                .select_related(
                    "beer__style",
                )
                .get()
            )
            self.assertEqual(tap.beer.name, "Coffee Perpetual Motion")
            self.assertEqual(tap.beer.abv, Decimal("9.0"))
            self.assertEqual(tap.gas_type, "")
            self.assertEqual(tap.beer.style.name, "Imperial Coffee Stout")
            self.assertEqual(
                tap.beer.untappd_url,
                "https://untappd.com/b/"
                "yellowhammer-brewing-coffee-perpetual-motion/4867930",
            )
            self.assertEqual(
                tap.beer.manufacturer.untappd_url,
                "https://untappd.com/brewery/8036",
            )
            self.assertEqual(
                tap.beer.logo_url,
                "https://utfb-images.untappd.com/"
                "q98tv8f15r77u77h84wgfp0iavd2?auto=compress",
            )
            prices = {
                Decimal(12): Decimal(8.0),
                Decimal(4): Decimal(5.0),
                Decimal(8): Decimal(7.0),
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
            mock_beer_lookup.delay.assert_called_with(tap.beer.id)
        self.venue.refresh_from_db()
        self.assertIsNotNone(self.venue.tap_list_last_check_time)
        self.assertGreater(self.venue.tap_list_last_check_time, timestamp)
        # Feb  5,  6:55 PM CST
        possible_timestamps = [
            # HACK: if we run this in January, it'll say the last updated time
            # is nearly a year ago because Untappd doesn't give us a year in
            # the timestamp (instead just "Jun 14,  9:45 AM CDT") and we rewind
            # by a year to avoid showing a last updated time in the future
            datetime.datetime(
                year, 6, 14, 9, 45, tzinfo=zoneinfo.ZoneInfo("America/Chicago")
            )
            for year in [now().year, now().year - 1]
        ]
        self.assertIn(self.venue.tap_list_last_update_time, possible_timestamps)


class StyleParsingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.belgian_ipa = StyleFactory(name="Belgian IPA")
        cls.english_cider = StyleFactory(name="English Cider")
        cls.farmhouse_ale = StyleFactory(
            name="foo", alternate_names=["Farmhouse Ale - Other"]
        )
        cls.parser = UntappdParser()

    def test_belgian_ipa(self):
        style = self.parser.parse_style("IPA - Belgian")
        self.assertEqual(style.id, self.belgian_ipa.id)

    def test_english_cider(self):
        style = self.parser.parse_style("Ciders and Meads - English Cider")
        self.assertEqual(style.id, self.english_cider.id)

    def test_farmhouse_ale(self):
        style = self.parser.parse_style("Farmhouse Ale - Other")
        self.assertEqual(style.id, self.farmhouse_ale.id)

    def test_kellerbier(self):
        style = self.parser.parse_style("Zwickelbier- German style Lager")
        # assert that we fix the name to add the missing space if nothing else
        self.assertEqual(style.name, "Zwickelbier - German style Lager")
