from django.test import TestCase
from beers.serializers import BeerStyleSerializer
from beers.models import BeerStyle

class BeerStyleSerializerTestCase(TestCase):
    def test_create(self):
        data = {
            'name': 'Test Style',
            'subcategory': 'A',
            'category': {
                'name': 'test category',
                'bjcp_class': 'beer',
                'category_id': '42'
            },
            'tags': [{'tag': 'test-tag'}]
        }
        serializer = BeerStyleSerializer(data=data)
        print(serializer)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertIsInstance(instance, BeerStyle)
        for field, value in data.items():
            with self.subTest(field=field):
                if field != 'category' and field != 'tags':
                    self.assertEqual(getattr(instance, field), value)
