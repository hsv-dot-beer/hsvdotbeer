from decimal import Decimal

from django.test import TestCase

from beers.serializers import ManufacturerSerializer, BeerSerializer
from beers.models import Manufacturer, Beer

from .factories import ManufacturerFactory, BeerFactory


class ManufacturerTestCase(TestCase):

    def test_create(self):
        data = {
            'name': 'your mother, Trebek',
            'url': 'https://example.com',
            'logo_url': 'https://example.com/logo.png',
            'facebook_url': 'https://facebook.com/yourmothertrebekbeer',
            'twitter_handle': 'yourmomtrebekbeer',
            'instagram_handle': 'whyamihere',
        }
        serializer = ManufacturerSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertIsInstance(instance, Manufacturer)
        for field, value in data.items():
            self.assertEqual(value, getattr(instance, field), field)
        self.assertIsNotNone(instance.time_first_seen)

    def test_update(self):
        instance = ManufacturerFactory()
        data = {'name': 'beerco'}
        serializer = ManufacturerSerializer(instance=instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance.refresh_from_db()
        self.assertEqual(instance.name, data['name'])


class BeerSerializerTestCase(TestCase):
    def test_create(self):
        manufacturer = ManufacturerFactory()
        data = {
            'manufacturer_id': manufacturer.id,
            'name': 'A beer',
            'color_srm': '27.7',
            'abv': '14.3',
            'ibu': 15,
        }
        serializer = BeerSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertIsInstance(instance, Beer)
        self.assertIsNotNone(instance.time_first_seen)
        self.assertEqual(instance.manufacturer, manufacturer)
        self.assertEqual(instance.name, data['name'])
        self.assertEqual(instance.color_srm, Decimal(data['color_srm']))
        self.assertEqual(instance.render_srm(), '#16100F')
        self.assertEqual(instance.abv, Decimal(data['abv']))
        self.assertEqual(instance.ibu, data['ibu'])

    def test_update(self):
        beer = BeerFactory()
        data = {
            'name': 'adsfasdsfa',
        }
        serializer = BeerSerializer(data=data, instance=beer, partial=True)
        serializer.is_valid()
        serializer.save()
        beer.refresh_from_db()
        self.assertEqual(beer.name, data['name'])

    def test_duplicate_beer(self):
        beer = BeerFactory()
        data = {
            'name': beer.name,
            'manufacturer_id': beer.manufacturer.id,
        }
        serializer = BeerSerializer(data=data)
        self.assertFalse(
            serializer.is_valid(raise_exception=False)
        )
