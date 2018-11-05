"""Base tap list provider

Children should subclass this and implement handle_venue()
which takes a single argument: a Venue object.

It'll have API configuration, rooms, taps, and existing beers prefetched.

TODO: implement those models.
"""

from venues.models import Venue


class BaseTapListProvider():

    def __init__(self):
        if not hasattr(self, 'provider_name'):
            # Don't define this attribute if the child does for us
            self.provider_name = None

    def handle_venue(self, venue):
        raise NotImplementedError('You need to implement this yourself')

    def get_venues(self):
        if not self.provider_name:
            raise ValueError(
                'You must define `provider_name` in your __init__()')
        queryset = Venue.objects.select_related(
            'api_configuration',
        ).filter(
            tap_list_provider=self.provider_name,
            api_configuration__isnull=False,
        )
        return queryset

    def handle_venues(self, venues):
        for venue in venues:
            self.handle_venue(venue)
