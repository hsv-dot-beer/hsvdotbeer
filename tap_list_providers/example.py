import json
import logging

from beers.models import Manufacturer, BeerStyleCategory
from taps.models import Tap

from .base import BaseTapListProvider

LOG = logging.getLogger(__name__)


class ExampleTapListProvider(BaseTapListProvider):
    """File-based tap list provider"""

    provider_name = 'test'

    def __init__(self, json_file):
        try:
            with open(json_file, 'r') as input_file:
                self.json_dict = json.loads(input_file.read())
        except (json.JSONDecodeError, IOError) as exc:
            print(f'Unable to read input file {json_file}: {exc}')
            raise
        super().__init__()

    def handle_venue(self, venue):
        LOG.info('Handling venue %s', venue)
        taps = {tap.tap_number: tap for tap in venue.taps.all()}
        names = set(i['brewery'] for i in self.json_dict['taps'].values())
        LOG.debug('Breweries: %s', names)
        manufacturers_qs = Manufacturer.objects.filter(
            name__in=list(names),
        )
        manufacturers = {i.name: i for i in manufacturers_qs.all()}
        LOG.debug('manufacturers: %s', list(manufacturers))
        for tap_number, beer_info in self.json_dict['taps'].items():
            try:
                tap = taps[int(tap_number)]
            except KeyError:
                tap = Tap.objects.create(
                    venue=venue,
                    tap_number=int(tap_number),
                )
                taps[tap.tap_number] = tap
            try:
                manufacturer = manufacturers[beer_info['brewery']]
            except KeyError:
                manufacturer = Manufacturer.objects.create(
                    name=beer_info['brewery'],
                )
                # cache it for next time
                manufacturers[manufacturer.name] = manufacturer
            name = beer_info.pop('beer')
            del beer_info['brewery']
            beer_info['style'] = self.guess_style(beer_info['style'])
            beer = self.get_beer(name, manufacturer, **beer_info)
            tap.beer = beer
            tap.save()

    def guess_style(self, style_name):
        """Attempt to guess a style based on the given name"""
        category, style = [i.strip() for i in style_name.split('-')]
        categories = BeerStyleCategory.objects.filter(
            name__iexact=category
        )
        try:
            style_category = categories.get()
        except BeerStyleCategory.DoesNotExist:
            LOG.warning('Could not find a match for category %s', category)
            return None
        candidate_styles = list(
            style_category.styles.filter(name__icontains=style)
        )
        if len(candidate_styles) == 1:
            matched_style = candidate_styles[0]
            LOG.debug('Matched %s to style %s', style_name, matched_style)
            return matched_style
        if not candidate_styles:
            LOG.warning('Could not find any matches for style %s', style_name)
            return None
        LOG.warning(
            'Found multiple matches for style %s: %s',
            style_name, candidate_styles,
        )
        return None
