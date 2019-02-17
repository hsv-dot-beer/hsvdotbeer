"""Base tap list provider

Children should subclass this and implement handle_venue()
which takes a single argument: a Venue object.

It'll have API configuration, rooms, taps, and existing beers prefetched.
"""
from decimal import Decimal
import logging

from django.db.models import Prefetch, Q

from venues.models import Venue, Room
from beers.models import Beer
from taps.models import Tap

LOG = logging.getLogger(__name__)


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
        LOG.debug(
            'Looking for venues with tap list provider %s', self.provider_name)
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
        LOG.debug(
            'get_beer(): name %s, mfg %s, defaults %s',
            name, manufacturer, defaults,
        )
        unique_fields = (
            'manufacturer_url', 'untappd_url', 'beer_advocate_url',
        )
        field_names = {i.name for i in Beer._meta.fields}
        bogus_defaults = set(defaults).difference(field_names)
        if bogus_defaults:
            raise ValueError(f'Unknown fields f{",".join(sorted(defaults))}')
        unique_fields_present = {
            field: value for field, value in defaults.items()
            if field in set(unique_fields) and value
        }
        beer = None
        if unique_fields_present:
            filter_expr = Q()
            for field, value in unique_fields_present.items():
                if value:
                    filter_expr |= Q(**{field: value})
            # get all possible matches
            # after moderation, this should only be one
            queryset = Beer.objects.filter(filter_expr)
            options = list(queryset)
            if len(options) > 1:
                # pick the one which has the preferred field set based on order
                for field in unique_fields_present:
                    for option in options:
                        if getattr(option, field):
                            beer = option
                            break
            elif options:
                beer = options[0]
            else:
                LOG.debug('No match found based on URL')
        try:
            abv = defaults.pop('abv')
        except KeyError:
            pass
        else:
            if isinstance(abv, str):
                if abv.endswith('%'):
                    abv = abv[:-1]
                abv = Decimal(abv)
            defaults['abv'] = abv
        if not beer:
            beer = Beer.objects.get_or_create(
                name=name,
                manufacturer=manufacturer,
                defaults=defaults,
            )[0]
        needs_update = False
        for field, value in defaults.items():
            # instead of using update_or_create(), only update fields *if*
            # they're set in `defaults`
            if value:
                if field.endswith('_url'):
                    if Beer.objects.exclude(id=beer.id).filter(
                        **{field: value}
                    ).exists():
                        LOG.warning(
                            'skipping updating %s (%s) for %s (PK %s) because it would'
                            ' conflict', field, value, beer.name, beer.id,
                        )
                        continue
                saved_value = getattr(beer, field)
                if value != saved_value:
                    # TODO mark as unmoderated
                    setattr(beer, field, value)
                    needs_update = True
        if needs_update:
            beer.save()
        return beer
