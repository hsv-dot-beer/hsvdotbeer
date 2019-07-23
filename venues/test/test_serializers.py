from django.test import TestCase
from venues.serializers import VenueSerializer, VenueAPIConfigurationSerializer
from venues.models import Venue, VenueAPIConfiguration
from .factories import VenueFactory


class VenueSerializerTestCase(TestCase):

    def test_create(self):
        data = {
            'name': 'My bar',
            'website': 'https://www.example.com',
            'instagram_handle': 'example',
            'time_zone': 'America/New_York',
            'slug': 'my-bar',
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

    def test_display_tap_list_provider(self):
        data = {
            'name': 'My bar',
            'website': 'https://www.example.com',
            'instagram_handle': 'example',
            'time_zone': 'America/New_York',
            'tap_list_provider': 'untappd',
            'slug': 'my-bar',
        }
        serializer = VenueSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertIsInstance(instance, Venue)
        serializer = VenueSerializer(instance=instance)
        self.assertEqual(
            serializer.data['tap_list_provider_display'], 'Untappd',
        )

    def test_bogus_latitude(self):
        data = {
            'name': 'My bar',
            'website': 'https://www.example.com',
            'instagram_handle': 'example',
            'time_zone': 'America/New_York',
            'tap_list_provider': 'untappd',
            'slug': 'my-bar',
            'latitude': 90.1,
            'longitude': 1,
        }
        serializer = VenueSerializer(data=data)
        self.assertFalse(serializer.is_valid(raise_exception=False))

    def test_bogus_longitude(self):
        data = {
            'name': 'My bar',
            'website': 'https://www.example.com',
            'instagram_handle': 'example',
            'time_zone': 'America/New_York',
            'tap_list_provider': 'untappd',
            'slug': 'my-bar',
            'latitude': 34.8,
            'longitude': 180.00001,
        }
        serializer = VenueSerializer(data=data)
        self.assertFalse(serializer.is_valid(raise_exception=False))


class VenueAPIConfigurationSerializerTestCase(TestCase):

    def setUp(self):
        self.venue = VenueFactory()

    def test_create(self):
        data = {
            'venue': self.venue.id,
            'url': 'https://example.com',
        }
        serializer = VenueAPIConfigurationSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertIsInstance(instance, VenueAPIConfiguration)
        self.assertEqual(instance.url, data['url'])
        self.assertEqual(instance.venue_id, self.venue.id)

    def test_display(self):
        instance = VenueAPIConfiguration.objects.create(
            venue=self.venue,
            url='https://foo.bar.example.com',
        )
        serializer = VenueAPIConfigurationSerializer(instance=instance)
        self.assertEqual(serializer.data['id'], instance.id)
        self.assertEqual(serializer.data['url'], instance.url)
        self.assertEqual(serializer.data['venue'], self.venue.id)
