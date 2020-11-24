"""Parse Arryved embedded menus"""

from django.core.management.base import BaseCommand
from django.db import transaction

from tap_list_providers.parsers.arryved_pos import ArryvedPOSParser


class Command(BaseCommand):
    help = "Populates any venues using the DigitalPour tap list provider with beers"

    def add_arguments(self, parser):
        # does not take any arguments
        pass

    def handle(self, *args, **options):
        tap_list_provider = ArryvedPOSParser()
        with transaction.atomic():
            for venue in tap_list_provider.get_venues():
                self.stdout.write("Processing %s" % venue.name)
                timestamp = tap_list_provider.handle_venue(venue)
                tap_list_provider.update_venue_timestamps(venue, timestamp)
        self.stdout.write(self.style.SUCCESS("Done!"))
