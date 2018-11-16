from django.test import TestCase
from venues.serializers import VenueSerializer, RoomSerializer, \
    VenueAPIConfigurationSerializer
from venues.models import Venue, VenueAPIConfiguration, Room
from .factories import VenueFactory


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

    def test_display_tap_list_provider(self):
        data = {
            'name': 'My bar',
            'website': 'https://www.example.com',
            'instagram_handle': 'example',
            'time_zone': 'America/New_York',
            'tap_list_provider': 'untappd',
        }
        serializer = VenueSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertIsInstance(instance, Venue)
        serializer = VenueSerializer(instance=instance)
        self.assertEqual(
            serializer.data['tap_list_provider_display'], 'Untappd',
        )


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


class RoomSerializerTestCase(TestCase):

    def setUp(self):
        self.venue = VenueFactory()
        # need to refresh from DB because the venue's time zone is a string
        # on factory build
        self.venue.refresh_from_db()

    def test_create(self):
        data = {
            'venue_id': self.venue.id,
            'name': 'The back room',
        }
        serializer = RoomSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertIsInstance(instance, Room)
        self.assertEqual(instance.description, '')
        self.assertEqual(instance.venue_id, self.venue.id)
        self.assertEqual(instance.name, data['name'])

    def test_display(self):
        instance = Room.objects.create(
            venue=self.venue,
            name='The front room',
        )
        serializer = RoomSerializer(instance=instance)
        self.assertEqual(instance.id, serializer.data['id'])
        venue = serializer.data['venue']
        self.assertEqual(instance.venue.id, venue['id'])
        self.assertEqual(
            venue, VenueSerializer(instance=self.venue).data,
        )
        self.assertEqual(serializer.data['description'], '')
