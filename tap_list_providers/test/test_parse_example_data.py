"""Test the parsing of example data"""

from django.core.management import call_command
from django.test import TestCase

from beers.models import Beer, Manufacturer
from venues.test.factories import VenueFactory, RoomFactory
from venues.models import Venue, VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.example import ExampleTapListProvider


class CommandsTestCase(TestCase):

    fixtures = ['example_style_data']

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory(
            tap_list_provider=ExampleTapListProvider.provider_name)
        cls.room = RoomFactory(venue=cls.venue)
        VenueAPIConfiguration.objects.create(
            venue=cls.venue, url='https://localhost:8000',
        )

    def test_import_data(self):
        """Test parsing the JSON data"""

        self.assertFalse(Tap.objects.exists())
        self.assertEqual(Venue.objects.count(), 1)
        self.assertFalse(Beer.objects.exists())
        self.assertFalse(Manufacturer.objects.exists())
        args = []
        opts = {}
        call_command('parseexampletaplist', *args, **opts)

        self.assertEqual(Beer.objects.count(), 3)
        self.assertEqual(Manufacturer.objects.count(), 3)
        self.assertEqual(Tap.objects.count(), 3)
        tap = Tap.objects.filter(room=self.room, tap_number=1).select_related(
            'beer__style',
        ).get()
        self.assertEqual(tap.beer.name, "Monkeynaut")
        self.assertEqual(tap.beer.style.name, 'American IPA')
