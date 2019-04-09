import json
import logging

from beers.models import Manufacturer
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
                manufacturer = self.get_manufacturer(name=beer_info['brewery'])
                # cache it for next time
                manufacturers[manufacturer.name] = manufacturer
            name = beer_info.pop('beer')
            del beer_info['brewery']
            beer_info['style'] = self.get_style(beer_info['style'])
            beer = self.get_beer(name, manufacturer, **beer_info)
            tap.beer = beer
            tap.save()
