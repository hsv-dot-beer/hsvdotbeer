from django.test import TestCase
from django.utils import timezone

from venues.test.factories import VenueFactory
from taps.serializers import TapSerializer
from taps.models import Tap
from .factories import TapFactory


class TapSerializerTestCase(TestCase):

    def test_create(self):
        venue = VenueFactory()
        data = {
            'tap_number': 42,
            'venue_id': venue.id,
            'time_added': timezone.now(),
            'time_updated': timezone.now()
        }
        serializer = TapSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.assertIsInstance(instance, Tap)
        self.assertEqual(instance.tap_number, data['tap_number'])
        self.assertEqual(instance.venue, venue)
        self.assertEqual(instance.gas_type, '')
        self.assertIsNone(instance.estimated_percent_remaining)

    def test_create_invalid_pct(self):
        venue = VenueFactory()
        data = {
            'tap_number': 42,
            'venue_id': venue.id,
            'estimated_percent_remaining': -1,
        }
        serializer = TapSerializer(data=data)
        self.assertFalse(serializer.is_valid(raise_exception=False))

    def test_create_duplicate(self):
        other = TapFactory()
        data = {
            'tap_number': other.tap_number,
            'venue_id': other.venue_id,
        }
        serializer = TapSerializer(data=data)
        self.assertFalse(serializer.is_valid(raise_exception=False))

    def test_update(self):
        tap = TapFactory()
        data = {'estimated_percent_remaining': 25}
        serializer = TapSerializer(data=data, instance=tap, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        tap.refresh_from_db()
        self.assertEqual(
            tap.estimated_percent_remaining,
            data['estimated_percent_remaining'],
        )
