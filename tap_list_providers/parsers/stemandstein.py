"""HTML scraper for The Stem & Stein"""
from urllib.parse import parse_qsl
from html.parser import HTMLParser
from decimal import Decimal
import logging
import os

from bs4 import BeautifulSoup
import requests
import configurations
from django.db.models import Q
from django.core.exceptions import ImproperlyConfigured, AppRegistryNotReady

# boilerplate code necessary for launching outside manage.py
try:
    from ..base import BaseTapListProvider
except (ImproperlyConfigured, AppRegistryNotReady):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'hsv_dot_beer.config'
    os.environ.setdefault("DJANGO_CONFIGURATION", "Local")
    configurations.setup()
    from ..base import BaseTapListProvider

from beers.models import Manufacturer, Beer, ServingSize, BeerPrice
from taps.models import Tap


LOG = logging.getLogger(__name__)


class StemAndSteinParser(BaseTapListProvider):
    """Parser for The Stem and Stein's static HTML page

    """

    provider_name = 'stemandstein'

    ROOT_URL = 'https://thestemandstein.com'
    BEER_URL = 'https://thestemandstein.com/Home/BeerDetails/{}'

    def __init__(self):
        self.html_parser = HTMLParser()
        self.parser = None
        self.serving_sizes = {
            i.volume_oz: i for i in ServingSize.objects.filter(
                volume_oz__in=[10, 16]
            )
        }
        if not self.serving_sizes or len(self.serving_sizes) != 2:
            raise ValueError('No serving sizes defined. Import fixtures!')
        self.venue = None
        super().__init__()

    def fetch_root_html(self):
        response = requests.get(self.__class__.ROOT_URL).text
        self.parser = BeautifulSoup(response, 'html.parser')

    def dump_html(self):
        print(self.parser.prettify())

    def parse_root_html(self):
        """Get a list of beer PKs to fetch"""
        beer_list = self.parser.find('ul', {'class': 'beerlist'})
        beers = [{
            'name': self.html_parser.unescape(tag.text),
            'url': tag.attrs['href'],
        } for tag in beer_list.find_all('a')]
        return beers

    def parse_beers(self, beers):
        """Fetch each beer, then attempt to guess the beer"""
        found_beers = {}
        for index, beer_dict in enumerate(beers):
            beer_pk = int(beer_dict['url'].split('/')[-1])
            beer = None
            try:
                beer = Beer.objects.get(stem_and_stein_pk=beer_pk)
            except Beer.DoesNotExist:
                # if we're really lucky, we can get a match by name
                try:
                    beer = Beer.objects.get(name=beer_dict['name'])
                except (Beer.DoesNotExist, Beer.MultipleObjectsReturned):
                    # womp womp
                    beer = self.guess_beer(beer_dict['name'])

            if beer.stem_and_stein_pk != beer_pk:
                beer.stem_and_stein_pk = beer_pk
                beer.save()
            found_beers[index + 1] = beer
        return found_beers

    def guess_manufacturer(self, beer_name, use_contains=False):
        words = beer_name.split(' ')
        # go in reverse order so we can catch longest name first
        for index in range(len(words) - 1, 0, -1):
            manufacturer = ' '.join(words[:index])
            if not use_contains:
                try:
                    return Manufacturer.objects.filter(
                        Q(name__iexact=manufacturer) |
                        Q(alternate_names__name__iexact=manufacturer)
                    ).distinct().get()
                except Manufacturer.DoesNotExist:
                    continue
            filter_str = 'icontains' if use_contains else 'istartswith'
            filter_expr = Q(**{
                f'name__{filter_str}': manufacturer,
            }) | Q(**{
                f'alternate_names__name__{filter_str}': manufacturer,
            })
            try:
                return Manufacturer.objects.filter(filter_expr)[0]
            except IndexError:
                continue
        if not use_contains:
            return self.guess_manufacturer(beer_name, use_contains=True)
        return None

    def guess_beer(self, beer_name):
        beer_name = beer_name.strip()
        manufacturer = self.guess_manufacturer(beer_name)
        if not manufacturer:
            manufacturer = Manufacturer.objects.create(
                name=beer_name.split(' ')[0]
            )
        beer_name = beer_name.replace(manufacturer.name, '').strip()
        return self.get_beer(name=beer_name, manufacturer=manufacturer)

    def fill_in_beer_details(self, beer):
        """Update color, serving size, and price for a beer"""
        beer_html = requests.get(
            self.__class__.BEER_URL.format(beer.stem_and_stein_pk),
        ).text
        beer_parser = BeautifulSoup(beer_html, 'html.parser')
        jumbotron = beer_parser.find('div', {'class': 'jumbotron'})
        image_div = jumbotron.find(
            'div',
            {'style': 'display:table-cell;vertical-align:top;width:17px;'},
        )
        pricing_div = jumbotron.find(
            'div',
            {
                'style': 'display: table-cell; padding: 3px;'
                ' font-size: 22px; vertical-align: top; width:42px',
            },
        )
        price = Decimal(pricing_div.text[1:])
        image_url = image_div.find('img').attrs['src']
        image_params = dict(parse_qsl(image_url.split('?')[-1]))
        abv_div = jumbotron.find(
            'div',
            {
                'style': 'color:slategray; font-size:18px;padding-left:20px',
            },
        )
        if not beer.abv:
            if 'ABV' in abv_div.text:
                # ABV x.y% (a bunch of spaces) city, state
                try:
                    abv = Decimal(abv_div.text.split()[1][:-1])
                except ValueError:
                    LOG.warning('Invalid S&S ABV %s for beer %s', abv_div.text, beer)
                else:
                    LOG.debug('Setting ABV for beer %s to %s%%', beer, abv)
                    beer.abv = abv
                    beer.save()
        if not beer.manufacturer.location:
            raw_text = abv_div.text.replace('&nbsp;', '')
            percent_index = raw_text.index('%')
            beer.manufacturer.location = raw_text[percent_index + 1:].strip()
            LOG.debug('Setting beer %s location to %s', beer, beer.manufacturer.location)
            beer.manufacturer.save()
        try:
            color = self.html_parser.unescape(image_params['color'])
        except KeyError:
            LOG.warning('Missing S&S color for beer %s', beer)
            color = None
        volume_oz = 16 if image_params[
            'glassware'
        ].casefold() == 'pint'.casefold() else 10
        if not beer.color_html and color:
            beer.color_html = color
            beer.save()
        serving_size = self.serving_sizes[volume_oz]
        BeerPrice.objects.update_or_create(
            venue=self.venue,
            serving_size=serving_size,
            beer=beer,
            defaults={'price': price},
        )

    def handle_venue(self, venue):
        self.venue = venue
        self.fetch_root_html()
        beers_found = self.parse_root_html()
        taps = self.parse_beers(beers_found)
        existing_taps = {
            i.tap_number: i for i in venue.taps.all()
        }
        LOG.debug('existing taps %s', existing_taps)
        taps_hit = []
        for tap_number, beer in taps.items():
            self.fill_in_beer_details(beer)
            try:
                tap = existing_taps[tap_number]
            except KeyError:
                tap = Tap(
                    venue=self.venue,
                    tap_number=tap_number,
                )
            tap.beer = beer
            tap.save()
            taps_hit.append(tap.tap_number)
        LOG.debug('Deleting all taps except %s', taps_hit)
        Tap.objects.filter(
            venue=venue,
        ).exclude(
            tap_number__in=taps_hit,
        ).delete()
