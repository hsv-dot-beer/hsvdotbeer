from django.test import TestCase

from beers.models import Beer, Manufacturer, BeerAlternateName, ManufacturerAlternateName
from taps.test.factories import TapFactory

from .factories import BeerFactory, ManufacturerFactory


class BeerTestCase(TestCase):

    def test_merge(self):
        manufacturer = ManufacturerFactory()
        beer1 = BeerFactory(
            manufacturer=manufacturer, untappd_url='http://localhost/123456',
            color_srm=None,
        )
        beer2 = BeerFactory(
            manufacturer=manufacturer, color_srm=55, stem_and_stein_pk=551,
        )
        tap = TapFactory(beer=beer2)
        beer1.merge_from(beer2)
        self.assertEqual(beer1.color_srm, beer2.color_srm)
        tap.refresh_from_db()
        self.assertEqual(tap.beer, beer1)
        self.assertFalse(Beer.objects.filter(id=beer2.id).exists())
        self.assertTrue(BeerAlternateName.objects.filter(
            name=beer2.name, beer=beer1,
        ).exists())
        self.assertEqual(tap.beer.stem_and_stein_pk, beer2.stem_and_stein_pk)


class ManufacturerTestCase(TestCase):

    def test_merge(self):
        mfg1 = ManufacturerFactory(
            untappd_url='http://localhost/123456', location='')
        mfg2 = ManufacturerFactory(location='your house')
        beer2 = BeerFactory(manufacturer=mfg2)
        mfg1.merge_from(mfg2)
        self.assertEqual(mfg1.location, mfg2.location)
        beer2.refresh_from_db()
        self.assertEqual(beer2.manufacturer, mfg1)
        self.assertFalse(Manufacturer.objects.filter(id=mfg2.id).exists())
        self.assertTrue(ManufacturerAlternateName.objects.filter(
            name=mfg2.name, manufacturer=mfg1,
        ).exists())
