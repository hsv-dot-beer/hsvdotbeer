"""Test DB constraints on beer model"""
from django.test import TestCase
from django.db.utils import IntegrityError, DataError

from beers.test.factories import BeerFactory


class BeerConstraintTestCase(TestCase):
    def test_negative_ibu(self):
        with self.assertRaises(IntegrityError):
            BeerFactory(ibu=-1)

    def test_high_ibu(self):
        with self.assertRaises(IntegrityError):
            BeerFactory(ibu=1001)

    def test_negative_abv(self):
        with self.assertRaises(IntegrityError):
            BeerFactory(abv=-1)

    def test_high_abv(self):
        with self.assertRaises(DataError):
            BeerFactory(abv=100.1)

    def test_srm_high(self):
        with self.assertRaises(IntegrityError):
            BeerFactory(color_srm=501)

    def test_srm_negative(self):
        with self.assertRaises(IntegrityError):
            BeerFactory(color_srm=-1)
