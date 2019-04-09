"""Test the parsing of example data"""
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from beers.models import Beer, Manufacturer
from beers.test.factories import StyleFactory, StyleAlternateNameFactory
from venues.test.factories import VenueFactory
from venues.models import Venue, VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.example import ExampleTapListProvider


class CommandsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory(
            tap_list_provider=ExampleTapListProvider.provider_name)
        VenueAPIConfiguration.objects.create(
            venue=cls.venue, url='https://localhost:8000',
        )
        ipa = StyleFactory(name='American IPA')
        StyleAlternateNameFactory(style=ipa, name='IPA - American')
        stout = StyleFactory(name='Sweet Stout')
        StyleAlternateNameFactory(style=stout, name='stout - milk')

    def test_import_example_data(self):
        """Test parsing the JSON data"""
        self.assertFalse(Tap.objects.exists())
        self.assertEqual(Venue.objects.count(), 1)
        self.assertFalse(Beer.objects.exists())
        self.assertFalse(Manufacturer.objects.exists())
        for dummy in range(2):
            # running twice to make sure we're not double-creating
            args = []
            opts = {}
            call_command('parseexampletaplist', *args, **opts)

            self.assertEqual(Beer.objects.count(), 3)
            self.assertEqual(Manufacturer.objects.count(), 3)
            self.assertEqual(Tap.objects.count(), 3)
            taps = Tap.objects.filter(
                venue=self.venue, tap_number__in=[1, 2],
            ).select_related(
                'beer__style',
            ).order_by('tap_number')
            tap = taps[0]
            self.assertEqual(tap.beer.name, "Monkeynaut")
            self.assertEqual(tap.beer.abv, Decimal('7.25'))
            self.assertEqual(tap.beer.style.name, 'American IPA')
            tap = taps[1]
            self.assertEqual(tap.beer.style.name, 'Sweet Stout')
