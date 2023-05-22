import datetime

from django.test import TestCase
from django.utils.timezone import now
from unittest import TestCase as UnittestTestCase

from tap_list_providers.base import fix_urls, BaseTapListProvider
from venues.test.factories import VenueFactory
from beers.test.factories import ManufacturerFactory, StyleFactory
from beers.models import Manufacturer


class URLFixTestCase(UnittestTestCase):
    def test_fix_urls(self):
        bad_data = {
            "beer_advocate_url": "http://www.ratebeer.com/beer/ace-pear-cider/3004/",
        }
        fix_urls(bad_data)
        self.assertEqual(
            bad_data,
            {
                "rate_beer_url": "http://www.ratebeer.com/beer/ace-pear-cider/3004/",
            },
        )


class ManufacturerTestCase(TestCase):
    def test_manufacturer_lookup(self):
        mfg = ManufacturerFactory(name="Stone")
        provider = BaseTapListProvider()
        for name in [
            "Stone Brewing Company",
            "Stone Brewing",
            "Stone",
            "Stone Beer Co.",
        ]:
            looked_up = provider.get_manufacturer(name)
            self.assertEqual(
                mfg,
                looked_up,
                f"{looked_up.name} does not match {name}",
            )
            self.assertEqual(Manufacturer.objects.count(), 1, name)

    def test_mfg_duplicate_alt_name(self):
        mfg = ManufacturerFactory(
            name="Founders", alternate_names=["Founders Brewing Co.", "Founders"]
        )
        provider = BaseTapListProvider()
        looked_up = provider.get_manufacturer(name=mfg.name)
        self.assertEqual(looked_up, mfg)


class TwitterHandleTestCase(TestCase):
    def test_twitter_handle(self):
        mfg = ManufacturerFactory(twitter_handle="abc123")
        provider = BaseTapListProvider()
        looked_up = provider.get_manufacturer(
            name=mfg.name,
            twitter_handle="https://twitter.com/foobar",
        )
        self.assertEqual(looked_up, mfg)
        self.assertEqual(looked_up.twitter_handle, "foobar")


class StyleTestCase(TestCase):
    def test_style_strip_none(self):
        provider = BaseTapListProvider()
        style = StyleFactory(name="test style")
        looked_up = provider.get_style("None - TEST STYLE")
        self.assertEqual(looked_up, style)


class FixBeerNameTestCase(TestCase):
    """Test reformatting beer names"""

    def test_standard(self):
        """Test the standard case"""
        provider = BaseTapListProvider()
        name = provider.reformat_beer_name("Stone IPA", "Stone")
        self.assertEqual(name, "IPA")

    def test_collab(self):
        """Test collaborations (See #321)"""
        provider = BaseTapListProvider()
        name = provider.reformat_beer_name(
            "Hi-Wire / New Belgium Belgian Stout", "Hi-Wire"
        )
        self.assertEqual(name, "Hi-Wire / New Belgium Belgian Stout")

    def test_yazoo(self):
        provider = BaseTapListProvider()
        name = provider.reformat_beer_name("Yazoo Brewing Company Hefeweizen", "Yazoo")
        self.assertEqual(name, "Hefeweizen")

    def test_brewery_equals_beer(self):
        provider = BaseTapListProvider()
        name = provider.reformat_beer_name("Weihenstephan", "Weihenstephan")
        self.assertEqual(name, "Weihenstephan")


class TimestampTestCase(TestCase):
    def setUp(self):
        self.venue = VenueFactory()
        self.provider = BaseTapListProvider()

    def test_initial_conditions(self):
        self.assertIsNone(self.venue.tap_list_last_check_time)
        self.assertIsNone(self.venue.tap_list_last_update_time)
        self.assertIsNotNone(self.provider.check_timestamp)

    def test_timestamp_no_time(self):
        self.provider.update_venue_timestamps(self.venue, None)
        self.assertIsNone(self.venue.tap_list_last_update_time)
        self.assertEqual(
            self.venue.tap_list_last_check_time, self.provider.check_timestamp
        )

    def test_with_time(self):
        timestamp = now() - datetime.timedelta(days=1)
        self.provider.update_venue_timestamps(self.venue, timestamp)
        self.assertEqual(self.venue.tap_list_last_update_time, timestamp)
        self.assertEqual(
            self.venue.tap_list_last_check_time, self.provider.check_timestamp
        )
