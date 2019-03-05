"""Test the parsing of digitalpour data"""
import json
import os
from decimal import Decimal

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

    fixtures = ['example_style_data']

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory(
            tap_list_provider=DigitalPourParser.provider_name)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue, url='https://localhost:8000',
            digital_pour_venue_id=12345,
            digital_pour_location_number=1,
        )
        with open(os.path.join(
            os.path.dirname(BASE_DIR),
            'tap_list_providers',
            'example_data',
            'rocket_city_craft_beer.json',
        ), 'rb') as json_file:
            cls.json_data = json.loads(json_file.read())

    @responses.activate
    def test_import_data(self):
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
        for dummy in range(2):
            # running twice to make sure we're not double-creating
            args = []
            opts = {}
            call_command('parsedigitalpour', *args, **opts)

            self.assertEqual(Beer.objects.count(), 4, list(Beer.objects.all()))
            self.assertEqual(Manufacturer.objects.count(), 4)
            self.assertEqual(Tap.objects.count(), 4)
            taps = Tap.objects.filter(
                venue=self.venue, tap_number__in=[22, 1, 2],
            ).select_related(
                'beer__style',
            ).order_by('tap_number')
            tap = taps[0]
            self.assertEqual(tap.beer.name, 'Hopslam')
            self.assertEqual(
                tap.beer.manufacturer_url,
                'https://www.bellsbeer.com/beer/specialty/hopslam-ale',
            )
            self.assertEqual(
                tap.beer.beer_advocate_url,
                "https://www.beeradvocate.com/beer/profile/287/17112/",
            )
            # location nulled out in test data
            self.assertEqual(tap.beer.manufacturer.location, '')
            tap = taps[2]
            self.assertEqual(tap.beer.name, "Milk Stout Nitro")
            self.assertEqual(tap.beer.abv, Decimal('6.0'))
            self.assertIsNone(tap.beer.style)
            self.assertEqual(tap.gas_type, 'nitro')
            self.assertEqual(tap.beer.render_srm(), '#241206')
            self.assertEqual(tap.beer.api_vendor_style, 'Milk Stout')
            prices = {
                Decimal(6.0): Decimal(3.0),
                Decimal(10.0): Decimal(5.0),
                Decimal(16.0): Decimal(8.0),
                Decimal(32.0): Decimal(13.5),
                Decimal(64.0): Decimal(25.0),
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
                self.assertEqual(
                    prices[price_instance.serving_size.volume_oz],
                    price_instance.price,
                    price_instance,
                )
            self.assertEqual(
                tap.beer.manufacturer.logo_url,
                'https://s3.amazonaws.com/digitalpourproducerlogos/4f7de8502595f5153887e925.png',
            )
            tap = taps[1]
            # This one has a ResolvedLogoImageUrl but LogoImageUrl is null
            self.assertEqual(tap.beer.name, 'POG Basement')
            self.assertEqual(
                tap.beer.logo_url,
                'https://s3.amazonaws.com/digitalpourproducerlogos/57ac9c3c5e002c172c8a6ede.jpg',
            )
