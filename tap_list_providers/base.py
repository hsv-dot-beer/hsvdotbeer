"""Base tap list provider

Children should subclass this and implement handle_venue()
which takes a single argument: a Venue object.

It'll have API configuration, taps, and existing beers prefetched.
"""
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse, unquote
import logging

from django.db.models import Prefetch, Q
from kombu.exceptions import OperationalError

from venues.models import Venue
from beers.models import Beer, Manufacturer, BeerPrice, ServingSize
from beers.tasks import look_up_beer
from taps.models import Tap
from .models import TapListProviderStyleMapping

LOG = logging.getLogger(__name__)

PROVIDER_BREWERY_LOGO_STRINGS = {
    'brewery_logos': 'Untappd',
    'digitalpourproducerlogos': 'DigitalPour',
}

COMMON_BREWERY_ENDINGS = (
    'Brewing Company',
    'Brewery',
    'Brewing',
    'Brewing Co.',
    'Brewing',
    'Beer Company',
    'Beer',
    'Beer Co.',
    'Craft Brewery',
)

REPLACE_TARGET = '\\.'
ENDINGS_REGEX = re.compile(
    f'({"|".join(i.replace(".", REPLACE_TARGET) for i in COMMON_BREWERY_ENDINGS)})$',
    re.IGNORECASE,
)


class BaseTapListProvider():

    def __init__(self):
        if not hasattr(self, 'provider_name'):
            # Don't define this attribute if the child does for us
            self.provider_name = None

    def handle_venue(self, venue):
        raise NotImplementedError('You need to implement this yourself')

    @classmethod
    def get_provider(cls, provider_name):
        """Get the class of provider that handles provider_name"""
        subclasses = {
            i.provider_name: i for i in cls.__subclasses__()
        }
        try:
            return subclasses[provider_name]
        except KeyError:
            raise ValueError(f'Unknown prover name {provider_name}')

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
                'taps',
                queryset=Tap.objects.select_related('beer__manufacturer'),
            ),
        )
        return queryset

    def handle_venues(self, venues):
        for venue in venues:
            LOG.debug('Fetching beers at %s', venue)
            self.handle_venue(venue)

    def get_beer(self, name, manufacturer, pricing=None, venue=None, **defaults):
        name = name.strip()
        LOG.debug(
            'get_beer(): name %s, mfg %s, defaults %s',
            name, manufacturer, defaults,
        )
        unique_fields = (
            'manufacturer_url', 'untappd_url', 'beer_advocate_url',
            'taphunter_url',
        )
        field_names = {i.name for i in Beer._meta.fields}
        bogus_defaults = set(defaults).difference(field_names)
        if bogus_defaults:
            raise ValueError(f'Unknown fields f{",".join(sorted(defaults))}')
        for key, val in list(defaults.items()):
            if val and key.endswith('_url'):
                unquoted = unquote(val)
                if unquoted != val:
                    LOG.debug(
                        'Replacing unquoted value for %s (%s) with %s',
                        key, val, unquoted,
                    )
                    defaults[key] = unquoted
        fix_urls(defaults)
        unique_fields_present = {
            field: value for field, value in defaults.items()
            if field in set(unique_fields) and value
        }
        serving_sizes = {i.volume_oz: i for i in ServingSize.objects.all()}
        try:
            api_vendor_style = defaults['api_vendor_style']
        except KeyError:
            # don't care; ignore it
            pass
        else:
            try:
                mapping = TapListProviderStyleMapping.objects.filter(
                    provider_style_name=api_vendor_style
                ).select_related('style').get()
            except TapListProviderStyleMapping.DoesNotExist:
                # oh well, it was worth a shot
                pass
            else:
                # go ahead and try to assign it to the style if possible
                defaults['style'] = mapping.style
                del defaults['api_vendor_style']
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
            try:
                beer = Beer.objects.get(
                    Q(name=name) | Q(alternate_names__name=name),
                    manufacturer=manufacturer,
                )
            except Beer.DoesNotExist:
                beer = Beer.objects.create(
                    name=name,
                    manufacturer=manufacturer,
                    **defaults,
                )
        needs_update = False
        if beer.logo_url and beer.logo_url == manufacturer.logo_url:
            beer.logo_url = None
            needs_update = True
        if not beer.automatic_updates_blocked:
            for field, value in defaults.items():
                # instead of using update_or_create(), only update fields *if*
                # they're set in `defaults`
                if not value or getattr(beer, field) == value:
                    # it's either unset or is already set to this value
                    continue
                if field == 'logo_url':
                    # these don't have to be unique
                    if beer.logo_url:
                        if venue and venue.tap_list_provider == 'taphunter':
                            LOG.info(
                                'Not trusting beer logo for %s from TapHunter'
                                ' because TH does not distinguish between '
                                'beer and brewery logos', beer
                            )
                            continue
                        found = False
                        for target, provider in PROVIDER_BREWERY_LOGO_STRINGS.items():
                            if target in value:
                                LOG.info(
                                    'Not overwriting logo for beer %s (%s) with brewery logo'
                                    ' from %s',
                                    beer, beer.logo_url, provider,
                                )
                                found = True
                                break
                        if found:
                            continue
                elif field.endswith('_url'):
                    if Beer.objects.exclude(id=beer.id).filter(
                        **{field: value}
                    ).exists():
                        LOG.warning(
                            'skipping updating %s (%s) for %s (PK %s)'
                            ' because it would conflict',
                            field, value, beer.name, beer.id,
                        )
                        continue
                saved_value = getattr(beer, field)
                if value != saved_value:
                    # TODO mark as unmoderated
                    setattr(beer, field, value)
                    needs_update = True
        if manufacturer.logo_url and not beer.logo_url:
            beer.logo_url = manufacturer.logo_url
            needs_update = True
        if needs_update:
            beer.save()
        if pricing:
            if not venue:
                raise ValueError('You must specify a venue with a price')
            for price_info in pricing:
                if price_info['price'] > 500:
                    LOG.warning(
                        'Skipping bogus price %s for %s oz of %s',
                        price_info['price'],
                        price_info['volume_oz'],
                        beer,
                    )
                    continue
                try:
                    serving_size = serving_sizes[price_info['volume_oz']]
                except KeyError:
                    serving_size = ServingSize.objects.get_or_create(
                        volume_oz=price_info['volume_oz'],
                        defaults={'name': price_info['name']},
                    )[0]
                    serving_sizes[price_info['volume_oz']] = serving_size
                try:
                    BeerPrice.objects.update_or_create(
                        serving_size=serving_size,
                        beer=beer,
                        venue=venue,
                        defaults={'price': price_info['price']}
                    )
                except InvalidOperation:
                    LOG.error(
                        'Unable to handle price %s for beer %s capacity %s',
                        price_info['price'], beer, serving_size)
                    raise
        if beer.untappd_url:
            # queue up an async fetch
            try:
                # if it has an untappd URL, queue a lookup for the next in line
                look_up_beer.delay(beer.id)
            except OperationalError as exc:
                if str(exc).casefold() == 'max number of clients reached'.casefold():
                    LOG.error('Reached redis limit!')
                    # fall back to doing it synchronously
                    look_up_beer(beer.id)
                else:
                    raise
        return beer

    def get_manufacturer(self, name, **defaults):
        name = ENDINGS_REGEX.sub('', name.strip()).strip()
        field_names = {i.name for i in Manufacturer._meta.fields}
        bogus_defaults = set(defaults).difference(field_names)
        if bogus_defaults:
            raise ValueError(f'Unknown fields f{",".join(sorted(defaults))}')
        kwargs = defaults.copy()
        manufacturer = None
        filter_expr = Q()
        unique_fields = {
            'untappd_url', 'taphunter_url',
        }
        for field in unique_fields:
            value = kwargs.get(field)
            if not value:
                continue
            if not manufacturer:
                options = list(Manufacturer.objects.filter(
                    Q(**{field: value}) | Q(name=name)
                ))
                if len(options) > 1:
                    LOG.info(
                        'Found multiple options for %s (%s %s)',
                        name, field, value,
                    )
                    # pick the one where the name matches
                    manufacturer = [
                        i for i in options if getattr(i, field)
                    ][0]
                elif options:
                    manufacturer = options[0]
        else:
            filter_expr = Q(name=name) | Q(alternate_names__name=name)
        if not manufacturer:
            LOG.debug(
                'looking up manufacturer with filter %s, args %s',
                filter_expr, kwargs,
            )
            try:
                manufacturer = Manufacturer.objects.get(filter_expr)
            except Manufacturer.DoesNotExist:
                manufacturer = Manufacturer.objects.create(
                    name=name, **kwargs)

        needs_update = False
        LOG.debug('Found manufacturer %s', manufacturer)
        if not manufacturer.automatic_updates_blocked:
            for field, value in defaults.items():
                if field == 'name':
                    # don't touch name
                    continue
                saved_value = getattr(manufacturer, field)
                if saved_value != value:
                    setattr(manufacturer, field, value)
                    needs_update = True
            if needs_update:
                LOG.debug('updating %s', manufacturer.name)
                manufacturer.save()
        return manufacturer


def fix_urls(defaults):
    """Make the URLs point to the right domains"""
    domain_map = {
        'rate_beer_url': 'ratebeer.com',
        'beer_advocate_url': 'beeradvocate.com',
        'untappd_url': 'untappd.com',
        'taphunter_url': 'taphunter.com',
    }

    for field, expected_domain in domain_map.items():
        try:
            given_value = defaults[field]
        except KeyError:
            # not given
            continue
        if not given_value:
            continue
        given_domain = urlparse(given_value).netloc
        if isinstance(given_domain, bytes):
            given_domain = given_domain.decode('utf-8')
        LOG.debug('Testing %s against %s', given_domain, expected_domain)
        if expected_domain not in given_domain:
            LOG.debug('no match')
            try:
                real_field = [
                    key for key, val in domain_map.items()
                    if val in given_domain
                ][0]
            except IndexError:
                LOG.warning(
                    'Unable to match %s to a known domain for %s',
                    given_value, field,
                )
            else:
                LOG.info(
                    'Switching %s from %s to %s',
                    given_value, field, real_field,
                )
                # don't care about handling the existing value;
                # odds are that data is bad too
                defaults[real_field] = defaults.pop(field)
