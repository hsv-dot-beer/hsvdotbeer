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
                "otbx.json",
            ),
            "rb",
        ) as json_file:
            cls.json_data = json.loads(json_file.read())

    @responses.activate
    def test_import_otbx_data(self):
        """Test fixing improper URL-quoting from OTBX"""
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
        for dummy in range(2):
            # running twice to make sure we're not double-creating
            args = []
            opts = {}
            call_command("parsedigitalpour", *args, **opts)
            self.assertEqual(Beer.objects.count(), 1, list(Beer.objects.all()))
            self.assertEqual(Manufacturer.objects.count(), 1)
            self.assertEqual(Tap.objects.count(), 1)
            taps = (
                Tap.objects.filter(
                    venue=self.venue,
                    tap_number=29,
                )
                .select_related(
                    "beer__style",
                )
                .order_by("tap_number")
            )
            tap = taps[0]
            self.assertEqual(tap.beer.name, "Hefe-Weisse")
            self.assertEqual(
                tap.beer.beer_advocate_url,
                "http://beeradvocate.com/beer/profile/142/924",
            )
            self.assertEqual(
                tap.beer.rate_beer_url,
                "http://www.ratebeer.com/beer/franziskaner-hefe-weissbier-dunkel/1089/",
            )
