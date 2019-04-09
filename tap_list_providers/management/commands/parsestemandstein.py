"""Parse the stem and stein tap list"""

from django.core.management.base import BaseCommand
from django.db import transaction

from tap_list_providers.parsers.stemandstein import StemAndSteinParser


class Command(BaseCommand):
    help = 'Populates any venues using the Stem and Stein tap list provider with' \
        ' beers'

    def add_arguments(self, parser):
        # does not take any arguments
        pass

    def handle(self, *args, **options):
        tap_list_provider = StemAndSteinParser()
        with transaction.atomic():
            for venue in tap_list_provider.get_venues():
                self.stdout.write('Processing %s' % venue.name)
                tap_list_provider.handle_venue(venue)
        self.stdout.write(self.style.SUCCESS('Done!'))
