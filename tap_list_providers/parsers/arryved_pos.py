"""Test parsing of Arryved embedded point of sale (PoS) menus"""

import datetime
from decimal import Decimal
import logging
import os
from typing import Dict, Union, Any, List

import requests
import configurations
from django.core.exceptions import ImproperlyConfigured, AppRegistryNotReady
from django.utils.timezone import now

# boilerplate code necessary for launching outside manage.py
try:
    from ..base import BaseTapListProvider
except (ImproperlyConfigured, AppRegistryNotReady):
    os.environ["DJANGO_SETTINGS_MODULE"] = "hsv_dot_beer.config"
    os.environ.setdefault("DJANGO_CONFIGURATION", "Local")
    configurations.setup()
    from ..base import BaseTapListProvider

from beers.models import Manufacturer, Beer, BeerPrice, ServingSize
from taps.models import Tap
from venues.models import Venue


LOG = logging.getLogger(__name__)


class ArryvedPOSParser(BaseTapListProvider):
    """Parser for Arrvyed embedded menus"""

    provider_name = "arryved_pos_menu"
    URL = "https://shop.arryved.com/preauthAction/getMenuOrderingData"

    def __init__(
        self,
        manufacturer: Manufacturer = None,
        location_id: str = None,
        serving_sizes: List[str] = None,
        menu_names: List[str] = None,
    ):
        self.location_id = location_id
        self.menu_names = set(menu_names or [])
        self.manufacturer = manufacturer
        self.serving_sizes = set(serving_sizes) if serving_sizes else set()

    def handle_venue(self, venue: Venue) -> datetime.datetime:
        timestamp = now()
        self.location_id = venue.api_configuration.arryved_location_id
        self.menu_names = set(venue.api_configuration.arryved_pos_menu_names)
        self.serving_sizes = set(venue.api_configuration.arryved_serving_sizes)
        BeerPrice.objects.filter(venue=venue).delete()
        try:
            self.manufacturer = Manufacturer.objects.get(
                name=venue.api_configuration.arryved_manufacturer_name
            )
        except Manufacturer.DoesNotExist as exc:
            raise ValueError(
                "You must create a manufacturer for "
                f"{venue.api_configuration.arryved_manufacturer_name or venue} before"
                " parsing!"
            ) from exc
        json_data = self.parse_json(self.fetch())
        taps = {i.tap_number: i for i in venue.taps.all()}
        manufacturer_beers = {
            beer.name: beer
            for beer in Beer.objects.filter(manufacturer=self.manufacturer)
        }
        prices = []
        serving_sizes = {i.volume_oz: i for i in ServingSize.objects.all()}
        tap_number = 1
        for beer in json_data["beers"]:
            tap = taps.get(tap_number, Tap(tap_number=tap_number, venue=venue))
            beer_created = False
            try:
                tap.beer = manufacturer_beers[beer["name"]]
            except KeyError:
                try:
                    tap.beer = Beer.objects.get(
                        manufacturer=self.manufacturer,
                        alternate_names__name=beer["name"],
                    )
                except Beer.DoesNotExist:
                    LOG.info("Creating beer %s for %s", beer["name"], self.manufacturer)
                    new_beer = Beer.objects.create(
                        manufacturer=self.manufacturer,
                        ibu=beer["ibu"],
                        abv=beer["abv"],
                        name=beer["name"],
                    )
                    tap.beer = new_beer
                    beer_created = True
            tap_prices = self.process_serving_sizes(
                tap.beer, venue, beer["serving_sizes"], serving_sizes
            )
            if not tap_prices:
                LOG.debug("Skipping beer %s because it is not on tap", tap.beer)
                if beer_created:
                    tap.beer.delete()
                continue
            prices += tap_prices
            if beer["ibu"]:
                tap.beer.ibu = beer["ibu"]
            if beer["abv"]:
                tap.beer.abv = beer["abv"]
            tap.time_updated = timestamp
            LOG.debug("Saving tap %s: %s", tap.tap_number, tap.beer)
            tap.save()
            tap_number += 1
        BeerPrice.objects.bulk_create(prices)
        self.check_timestamp = None

    def process_serving_sizes(
        self,
        beer: Beer,
        venue: Venue,
        pricing_data: List[Dict],
        serving_sizes: Dict[Decimal, ServingSize],
    ) -> List[BeerPrice]:
        result = []
        for size_dict in pricing_data:
            LOG.debug("size dict: %s", size_dict)
            capacity = Decimal(size_dict["size"])
            price = size_dict["price"]
            try:
                serving_size = serving_sizes[Decimal(capacity)]
            except KeyError:
                serving_size = ServingSize.objects.create(
                    name=f"{capacity} oz",
                    volume_oz=capacity,
                )
                serving_sizes[capacity] = serving_size
            result.append(
                BeerPrice(
                    beer=beer,
                    venue=venue,
                    serving_size=serving_size,
                    price=price,
                )
            )
            LOG.debug(
                "Beer %s (%s) costs %s for serving size %s (PK %s)",
                beer.id,
                beer.name,
                price,
                capacity,
                serving_size.id,
            )
        return result

    def fetch(self):
        response = requests.post(
            self.URL,
            json={
                "locationId": self.location_id,
                "versionInfo": {"clientVersion": "6.4", "requestApi": 6},
                "orderModality": "pickup",
                "requestId": "n8qZDyArL03LjVfP",
            },
        )
        response.raise_for_status()
        return response.json()

    def parse_json(self, json_data: Dict[str, Any]):
        payload = json_data["payload"]
        beers = self.parse_items(payload)
        return {
            "beers": beers,
        }

    def parse_items(
        self,
        payload: Dict[str, Dict],
    ) -> List[Dict[str, Union[str, int, float]]]:
        result = []
        for menu in payload["menus"]:
            if menu["displayName"] not in self.menu_names:
                continue
            for item in menu["availableItems"]:
                result.append(
                    {
                        "pk": item["itemId"],
                        "name": item["displayName"],
                        "serving_sizes": [
                            {
                                "size": self.parse_size(size),
                                # price is in cents
                                "price": size["price"] / 100,
                            }
                            for size in item["sizes"]
                            if size["sizeCode"] in self.serving_sizes
                        ],
                        "abv": Decimal(item["abv"]) if item["abv"] else None,
                        "ibu": int(item["ibu"]) if item["ibu"] else None,
                    }
                )
        return result

    def parse_size(
        self, serving_size: Dict[str, Union[int, str, List]]
    ) -> Union[int, float]:
        raw_size = serving_size["sizeDisplayName"].split("oz")[0]
        try:
            return int(raw_size)
        except ValueError:
            return float(raw_size)
