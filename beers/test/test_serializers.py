from django.test import TestCase
from beers.serializers import BeerStyleSerializer
from beers.models import BeerStyle

class BeerStyleSerializerTestCase(TestCase):
    def test_create(self):
        data = {
            'name': 'Test Style',
            'category': '42',
            'subcategory': 'A',
            'category_name': 'Super Light',
            'category_notes': 'Super Light',
        }
        serializer = BeerStyleSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertIsInstance(instance, BeerStyle)
