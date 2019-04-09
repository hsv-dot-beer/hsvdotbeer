"""Parse the example tap list as if it were a real bar"""
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from hsv_dot_beer.config.local import BASE_DIR
from tap_list_providers.example import ExampleTapListProvider


class Command(BaseCommand):
    help = 'Populates any venues using the example tap list provider with' \
        ' beers'

    DEFAULT_JSON_FILE = os.path.join(
        os.path.dirname(BASE_DIR),
        'tap_list_providers',
        'example_data',
        'beer.json',
    )

    def add_arguments(self, parser):
        parser.add_argument('--input', default=self.DEFAULT_JSON_FILE)

    def handle(self, *args, **options):
        tap_list_provider = ExampleTapListProvider(options['input'])
        with transaction.atomic():
            for venue in tap_list_provider.get_venues():
                self.stdout.write('Processing %s' % venue.name)
                tap_list_provider.handle_venue(venue)
        self.stdout.write(self.style.SUCCESS('Done!'))
