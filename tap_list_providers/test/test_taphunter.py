"""Test the parsing of taphunter data"""
import os
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
import responses

from beers.models import Beer, Manufacturer
from venues.test.factories import VenueFactory
from venues.models import Venue, VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.parsers.taphunter import TaphunterParser
from hsv_dot_beer.config.local import BASE_DIR


class CommandsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory(
            tap_list_provider=TaphunterParser.provider_name)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue, url='https://localhost:8000',
            taphunter_location=12345,
        )
        with open(os.path.join(
            os.path.dirname(BASE_DIR),
            'tap_list_providers',
            'example_data',
            'liquor_express.json',
        ), 'rb') as json_file:
            cls.json_data = json_file.read()

    @responses.activate
    def test_import_taphunter_data(self):
        """Test parsing the JSON data"""
        responses.add(
            responses.GET,
            TaphunterParser.URL.format(
                self.venue_cfg.taphunter_location
            ),
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
            call_command('parsetaphunter', *args, **opts)

            self.assertEqual(Beer.objects.count(), 93)
            self.assertEqual(Manufacturer.objects.count(), 52)
            self.assertEqual(Tap.objects.count(), 93)
            taps = Tap.objects.filter(
                venue=self.venue, tap_number__in=[6, 22],
            ).select_related(
                'beer__style', 'beer__manufacturer',
            ).order_by('tap_number')
            tap = taps[0]
            self.assertEqual(tap.beer.name, 'Crisp Apple Cider', tap.beer)
            self.assertEqual(
                tap.beer.manufacturer.name, 'Angry Orchard Cidery', tap.beer.manufacturer,
            )
            self.assertEqual(
                tap.beer.logo_url,
                "https://lh3.googleusercontent.com/Pd6YLv5-aHD6nkNnTZBA1VzjHgYkf"
                "-Y7axHi0d6EvSOlV-0OEbI4FIn7CHssVtuFN4l7FzKZztU_X_c8rgAclWlEylvCvqs=s150",
            )
            self.assertEqual(
                tap.beer.taphunter_url,
                "https://www.taphunter.com/beer/"
                "angry-orchard-crisp-apple-cider/48961206",
            )
            self.assertEqual(
                tap.beer.manufacturer.logo_url,
                "https://lh5.ggpht.com/gUNebXp4obondztO0FPSxhFGr1JFMKMv2TnXvk5I"
                "_A4UQpd4YSs-PTjWBHP1HDivT8O10rPENIwfMXjg9NaaMsrAp6p6Rw=s150",
            )
            self.assertEqual(
                tap.beer.manufacturer.taphunter_url,
                'https://www.taphunter.com/brewery/angry-orchard-cidery/'
                '35527549',
            )
            tap = taps[1]
            self.assertEqual(tap.beer.name, "Bound By Time")
            self.assertEqual(tap.beer.abv, Decimal('7.00'))
            self.assertEqual(tap.gas_type, '')
            self.assertEqual(
                tap.beer.logo_url,
                "https://lh3.googleusercontent.com/"
                "1vjvIHZY1bAHPNvP6-z74EaZWVx3IfJU6wO3VFhSJlvVKuBmJ68ZOKI6r"
                "Y1c6uyGluAVvK2Qhpq5WfdbO7ArKF4ZS9OdZA=s150",
            )
            prices = {
                Decimal(12): Decimal(5.99),
                Decimal(16): Decimal(7.99),
                Decimal(32): Decimal(9.59),
            }
            price_instances = list(tap.beer.prices.select_related('serving_size', 'venue'))
            self.assertEqual(
                len(price_instances),
                len(prices),
                price_instances,
            )
            for price_instance in price_instances:
                self.assertEqual(price_instance.venue, self.venue, price_instance)
                self.assertIn(price_instance.serving_size.volume_oz, prices, price_instance)
                # because DigitalPour passes prices as floats, we will have
                # floating-point errors in test. These won't show in production
                # because the database rounds for us
                self.assertAlmostEqual(
                    prices[price_instance.serving_size.volume_oz],
                    price_instance.price,
                    3,
                    price_instance,
                )
