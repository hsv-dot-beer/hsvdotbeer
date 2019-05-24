"""Verify that purging beer prices works as expected"""

from django.test import TestCase

from taps.models import Tap
from venues.test.factories import VenueFactory
from taps.test.factories import TapFactory
from beers.models import BeerPrice, Beer
from beers.tasks import purge_unused_prices
from beers.test.factories import BeerFactory, ManufacturerFactory


class PricePurgeTestCase(TestCase):

    fixtures = ['serving_sizes']

    def setUp(self):
        manufacturer = ManufacturerFactory()
        venue = VenueFactory()
        self.beers = Beer.objects.bulk_create(
            BeerFactory.build(
                manufacturer=manufacturer,
            ) for dummy in range(20)
        )
        self.prices = BeerPrice.objects.bulk_create(
            BeerPrice(
                # pint
                serving_size_id=1,
                price=index * 2.1,
                beer=beer,
                venue=venue,
            ) for index, beer in enumerate(self.beers)
        )
        self.taps = Tap.objects.bulk_create(
            # only for half of them
            TapFactory.build(beer=beer, venue=venue)
            for beer in self.beers[:10]
        )

    def test_purge(self):
        self.assertEqual(BeerPrice.objects.count(), len(self.prices))
        purge_unused_prices()
        # since I only created one price per tap, the number of taps will
        # equal the number of prices remaining
        self.assertEqual(BeerPrice.objects.count(), len(self.taps))
        self.assertFalse(BeerPrice.objects.filter(
            beer__taps__isnull=True,
        ).exists())
