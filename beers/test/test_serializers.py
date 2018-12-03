from decimal import Decimal

from django.test import TestCase

from beers.serializers import BeerStyleSerializer, ManufacturerSerializer, \
    BeerSerializer
from beers.models import BeerStyle, Manufacturer, Beer

from .factories import BeerStyleCategoryFactory, BeerStyleFactory, \
    BeerStyleTagFactory, ManufacturerFactory, BeerFactory


class BeerStyleSerializerTestCase(TestCase):

    def test_create(self):
        cat = BeerStyleCategoryFactory()
        data = {
            'name': 'Test Style',
            'subcategory': 'A',
            'category_id': cat.id,
            'tags': [{'tag': 'test-tag'}]
        }
        serializer = BeerStyleSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertIsInstance(instance, BeerStyle)
        for field, value in data.items():
            with self.subTest(field=field):
                if field != 'category' and field != 'tags':
                    self.assertEqual(getattr(instance, field), value)

    def test_create_invalid_ibu(self):
        cat = BeerStyleCategoryFactory()
        data = {
            'name': 'Test Style',
            'subcategory': 'A',
            'category_id': cat.id,
            'ibu_low': 10,
            'ibu_high': 5,
            'tags': [{'tag': 'test-tag'}]
        }
        serializer = BeerStyleSerializer(data=data)
        self.assertFalse(serializer.is_valid(raise_exception=False))

    def test_update(self):
        style = BeerStyleFactory()
        tags = [BeerStyleTagFactory() for dummy in range(5)]
        self.assertEqual(style.tags.count(), 0)
        style.tags.set(tags, clear=True)
        self.assertEqual(style.tags.count(), 5)
        data = {'tags': []}
        serializer = BeerStyleSerializer(data=data, instance=style, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        style.refresh_from_db()
        self.assertEqual(style.tags.count(), 0)


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
