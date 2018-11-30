import datetime

from pytz import UTC
from django.test import TestCase
from rest_framework.serializers import DateTimeField

from events.serializers import EventSerializer
from events.models import Event
from venues.serializers import VenueSerializer
from venues.test.factories import VenueFactory


class EventSerializerTestCase(TestCase):

    def setUp(self):
        self.venue = VenueFactory()
        self.venue.refresh_from_db()

    def test_create(self):
        data = {
            'title': 'bike night',
            'start_time': '2018-10-15T11:12:34+00:00',
            'end_time': '2018-10-16T00:00:00+00:00',
            'description': 'No',
            'venue_id': self.venue.id,
        }
        serializer = EventSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertIsInstance(instance, Event)
        for field, value in data.items():
            with self.subTest(field=field):
                original = getattr(instance, field)
                if isinstance(original, datetime.datetime):
                    original = original.isoformat()
                self.assertEqual(original, value, field)

    def test_invalid_time(self):
        data = {
            'title': 'beer and kittens',
            'end_time': '2018-10-15T11:12:34Z',
            'start_time': '2018-10-16T00:00:00Z',
            'description': 'No',
            'venue_id': self.venue.id,
        }
        serializer = EventSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_display(self):
        instance = Event.objects.create(
            title='test',
            venue=self.venue,
            start_time=UTC.localize(datetime.datetime(2018, 11, 20, 12)),
            end_time=UTC.localize(datetime.datetime(2018, 11, 20, 16)),
        )
        serializer = EventSerializer(instance=instance)
        for field, value in serializer.data.items():
            if field == 'venue':
                self.assertEqual(
                    value,
                    VenueSerializer(self.venue).data,
                    field,
                )
            elif field.endswith('_time'):
                self.assertEqual(
                    value,
                    DateTimeField().to_representation(
                        getattr(instance, field),
                    ),
                    field,
                )
            else:
                self.assertEqual(value, getattr(instance, field), field)
