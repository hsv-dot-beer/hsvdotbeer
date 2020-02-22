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
from django.db.models.functions import Length
from django.db import transaction
from kombu.exceptions import OperationalError

from venues.models import Venue
from beers.models import Beer, Manufacturer, BeerPrice, ServingSize, Style
from beers.tasks import look_up_beer
from taps.models import Tap

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
        self.styles = {}
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

    def get_style(self, name):
        name = name.strip()
        if name == '-':
            # bogus untappd style
            return None
        if name.startswith('None - '):
            # strip untappd noise
            name = name[7:]
        try:
            return self.styles[name.casefold()]
        except KeyError:
            # do it the old fashioned way
            pass
        with transaction.atomic():
            try:
                style = Style.objects.get(name=name)
            except Style.DoesNotExist:
                try:
                    style = Style.objects.get(alternate_names__name=name)
                except Style.DoesNotExist:
                    style = Style.objects.create(name=name, default_color='')
        self.styles[name.casefold()] = style
        return style

    def reformat_beer_name(self, name: str, mfg_name: str) -> str:
        """Try to strip the manufacturer name if possible"""
        original_name = name.strip()
        name = name.replace(mfg_name, '').strip()
        if name.startswith(tuple('/-_')):
            # it's likely a collaboration beer. Put the manufacturer back in there.
            name = original_name
        return name

    def guess_style(self, beer_name):
        """Try to guess the style from the beer name"""
        ci_name = beer_name.casefold()
        for name, style in sorted(
            self.styles.items(), key=lambda k: len(k[0]), reverse=True,
        ):
            if name in ci_name:
                LOG.debug('Guessed style %s for beer %s', style, beer_name)
                return style
        alt_names = []
        for style in self.styles.values():
            alt_names += list(
                (i.name.casefold(), style)
                for i in style.alternate_names.all()
            )
        for alt_name, style in sorted(
            alt_names, key=lambda k: len(k[0]), reverse=True,
        ):
            if alt_name in ci_name:
                LOG.debug('Guessed alternate style %s for beer %s', style, beer_name)
                return style
        LOG.info('Could not find a style for beer %s', beer_name)

    def fetch_styles(self):
        self.styles = {
            style.name.casefold(): style
            for style in Style.objects.prefetch_related(
                'alternate_names',
            ).annotate(
                name_chars=Length('name')
            ).order_by('-name_chars')
        }

    def get_beer(self, name, manufacturer, pricing=None, venue=None, **defaults):
        if not self.styles:
            self.fetch_styles()
        name = name.strip()
        LOG.debug(
            'get_beer(): name %s, mfg %s, defaults %s',
            name, manufacturer, defaults,
        )
        mfg_name = manufacturer.name
        for ending in COMMON_BREWERY_ENDINGS:
            if mfg_name.endswith(ending):
                mfg_name = mfg_name.replace(ending, '').strip()
        name = self.reformat_beer_name(name, mfg_name)
        unique_fields = (
            'manufacturer_url', 'untappd_url', 'beer_advocate_url',
            'taphunter_url', 'taplist_io_pk', 'beermenus_slug',
        )
        field_names = {i.name for i in Beer._meta.fields}
        bogus_defaults = set(defaults).difference(field_names)
        if bogus_defaults:
            raise ValueError(
                f'Unknown field(s) {", ".join(sorted(bogus_defaults))}'
            )
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
        if 'style' in defaults and not isinstance(defaults['style'], Style):
            defaults['style'] = self.get_style(defaults['style'])
        elif not defaults.get('style'):
            defaults['style'] = self.guess_style(name)
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
                beer = Beer.objects.filter(
                    Q(name=name) | Q(alternate_names__name=name),
                    manufacturer=manufacturer,
                ).distinct().get()
                LOG.debug('looked up %s for %s', beer, name)
            except Beer.DoesNotExist:
                LOG.debug('beer %s not found', name)
                beer = None
                if defaults.get('style') and defaults[
                    'style'
                ].name.casefold() in name.casefold():
                    subbed_name = re.sub(
                        rf'\s{defaults["style"].name}$',
                        '',
                        name,
                        flags=re.IGNORECASE,
                    ).strip()
                    try:
                        beer = Beer.objects.filter(
                            Q(name=subbed_name) | Q(alternate_names__name=subbed_name),
                            manufacturer=manufacturer,
                        ).distinct().get()
                    except Beer.DoesNotExist:
                        LOG.debug('Substituted name %s does not exist', subbed_name)
                    else:
                        LOG.debug('Successfully replaced %s with %s', name, beer)
                if not beer:
                    beer = Beer.objects.create(
                        name=name,
                        manufacturer=manufacturer,
                        **defaults,
                    )
            except Beer.MultipleObjectsReturned:
                LOG.error(
                    'Found duplicate results for name %s from mfg %s!',
                    name, manufacturer,
                )
                # just take the first one
                beer = Beer.objects.filter(
                    Q(name=name) | Q(alternate_names__name=name),
                    manufacturer=manufacturer,
                )[0]
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
            beer.prices.filter(venue=venue).delete()
            for price_info in pricing:
                if price_info['price'] > 500:
                    LOG.warning(
                        'Skipping bogus price %s for %s oz of %s',
                        price_info['price'],
                        price_info['volume_oz'],
                        beer,
                    )
                    continue
                LOG.debug('Rounding volume')
                price_info['volume_oz'] = Decimal(
                    round(price_info['volume_oz'], 1)
                )
                try:
                    serving_size = serving_sizes[price_info['volume_oz']]
                except KeyError:
                    serving_size = ServingSize.objects.get_or_create(
                        volume_oz=price_info['volume_oz'],
                        defaults={'name': price_info['name']},
                    )[0]
                    serving_sizes[price_info['volume_oz']] = serving_size
                try:
                    BeerPrice.objects.create(
                        serving_size=serving_size,
                        beer=beer,
                        venue=venue,
                        price=price_info['price'],
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
            'untappd_url', 'taphunter_url', 'taplist_io_pk', 'beermenus_slug',
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
                manufacturer = Manufacturer.objects.filter(
                    filter_expr
                ).distinct().get()
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
