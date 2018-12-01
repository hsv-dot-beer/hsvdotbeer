from django.test import TestCase
from beers.serializers import BeerStyleSerializer
from beers.models import BeerStyle

from .factories import BeerStyleCategoryFactory

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
