from django.test import TestCase
from venues.serializers import VenueSerializer
from venues.models import Venue


class VenueSerializerTestCase(TestCase):

    def test_create(self):
        data = {
            'name': 'My bar',
            'website': 'https://www.example.com',
            'instagram_handle': 'example',
            'time_zone': 'America/New_York',
        }
        serializer = VenueSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertIsInstance(instance, Venue)
        for field, value in data.items():
            with self.subTest(field=field):
                if field != 'time_zone':
                    self.assertEqual(getattr(instance, field), value)
                else:
                    self.assertEqual(instance.time_zone.zone, value)
