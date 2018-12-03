from django.test import TestCase
from beers.serializers import BeerStyleSerializer, ManufacturerSerializer
from beers.models import BeerStyle, Manufacturer

from .factories import BeerStyleCategoryFactory, BeerStyleFactory, \
    BeerStyleTagFactory, ManufacturerFactory


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
