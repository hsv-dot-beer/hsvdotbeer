import datetime

from django.test import TestCase

from beers.models import (
    Beer,
    Manufacturer,
    BeerPrice,
    ServingSize,
)
from taps.models import Tap
from taps.test.factories import TapFactory
from venues.models import Venue
from venues.test.factories import VenueFactory

from .factories import BeerFactory, ManufacturerFactory


class BeerTestCase(TestCase):
    def setUp(self):
        self.manufacturer: Manufacturer = ManufacturerFactory()
        self.new_time = datetime.datetime(
            2018,
            4,
            3,
            6,
            2,
            tzinfo=datetime.timezone.utc,
        )
        self.other_time = self.new_time + datetime.timedelta(days=30)
        self.beer1: Beer = BeerFactory(
            manufacturer=self.manufacturer,
            untappd_url="http://localhost/123456",
            color_srm=None,
            time_first_seen=self.other_time,
        )
        self.beer2: Beer = BeerFactory(
            manufacturer=self.manufacturer,
            color_srm=55,
            stem_and_stein_pk=551,
            time_first_seen=self.new_time,
        )
        self.tap: Tap = TapFactory(beer=self.beer2)
        self.venue2 = self.tap.venue
        self.venue1: Venue = VenueFactory()
        self.serving_size: ServingSize = ServingSize.objects.create(
            name="foo", volume_oz=12
        )

    def test_merge(self):
        self.beer1.merge_from(self.beer2)
        self.assertEqual(self.beer1.color_srm, self.beer2.color_srm)
        self.tap.refresh_from_db()
        self.assertEqual(self.tap.beer, self.beer1)
        self.assertFalse(Beer.objects.filter(id=self.beer2.id).exists())
        self.assertEqual(self.beer1.alternate_names, [self.beer2.name])
        self.assertEqual(self.tap.beer.time_first_seen, self.new_time)
        self.assertEqual(self.tap.beer.stem_and_stein_pk, 551)

    def test_preserve_prices_no_overlap(self):
        BeerPrice.objects.create(
            beer=self.beer1,
            venue=self.venue1,
            price=15,
            serving_size=self.serving_size,
        )
        BeerPrice.objects.create(
            beer=self.beer2,
            venue=self.venue2,
            price=10,
            serving_size=self.serving_size,
        )
        self.beer1.merge_from(self.beer2)
        self.assertEqual(BeerPrice.objects.filter(beer=self.beer1).count(), 2)

    def test_preserve_prices_overlap(self):
        BeerPrice.objects.create(
            beer=self.beer1,
            venue=self.venue2,
            price=15,
            serving_size=self.serving_size,
        )
        BeerPrice.objects.create(
            beer=self.beer2,
            venue=self.venue2,
            price=10,
            serving_size=self.serving_size,
        )
        other_size = ServingSize.objects.create(name="bar", volume_oz=16)
        BeerPrice.objects.create(
            beer=self.beer2,
            venue=self.venue2,
            price=20,
            serving_size=other_size,
        )
        self.beer1.merge_from(self.beer2)
        # Because we have an overlap in one unique condition (beer + venue + size),
        # we are going to take the safest route possible and ignore both of the
        # prices from beer2 for venue2.
        self.assertEqual(BeerPrice.objects.filter(beer=self.beer1).count(), 1)


class ManufacturerTestCase(TestCase):
    def test_merge(self):
        new_time = datetime.datetime(2018, 4, 3, 6, 2, tzinfo=datetime.timezone.utc)
        other_time = new_time + datetime.timedelta(days=30)
        mfg1: Manufacturer = ManufacturerFactory(
            untappd_url="http://localhost/123456",
            location="",
            time_first_seen=other_time,
        )
        mfg2: Manufacturer = ManufacturerFactory(
            location="your house",
            time_first_seen=new_time,
        )
        beer2 = BeerFactory(manufacturer=mfg2)
        mfg1.merge_from(mfg2)
        self.assertEqual(mfg1.location, mfg2.location)
        self.assertEqual(mfg1.alternate_names, [mfg2.name])
        beer2.refresh_from_db()
        self.assertEqual(beer2.manufacturer, mfg1)
        self.assertFalse(Manufacturer.objects.filter(id=mfg2.id).exists())
        self.assertEqual(beer2.manufacturer.time_first_seen, new_time)
