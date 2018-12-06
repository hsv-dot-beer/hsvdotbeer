"""Base tap list provider

Children should subclass this and implement handle_venue()
which takes a single argument: a Venue object.

It'll have API configuration, rooms, taps, and existing beers prefetched.
"""

from django.db.models import Prefetch

from venues.models import Venue, Room
from beers.model import Beer
from taps.models import Tap


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
        ).prefetch_related(
            Prefetch(
                'rooms',
                queryset=Room.objects.prefetch_related(
                    Prefetch(
                        'taps__beer__manufacturer',
                        queryset=Tap.objects.select_related(
                            'beer__manufacturer',
                            'beer__style__category',
                        ),
                    ),
                ),
            ),
        )
        return queryset

    def handle_venues(self, venues):
        for venue in venues:
            self.handle_venue(venue)

    def get_beer(self, name, manufacturer, **defaults):
        field_names = {i.name for i in Beer._meta.fields}
        bogus_defaults = set(defaults).difference(field_names)
        if bogus_defaults:
            raise ValueError(f'Unknown fields f{",".join(sorted(defaults))}')
        beer = Beer.objects.get_or_create(
            name=name,
            manufacturer=manufacturer,
            defaults=defaults,
        )[0]
        return beer
