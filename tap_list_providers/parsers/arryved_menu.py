"""Parser for Arryved embedded menus"""
from collections import defaultdict
import datetime
from decimal import Decimal
import logging
import os
from typing import Any

import requests
import configurations
from django.core.exceptions import ImproperlyConfigured, AppRegistryNotReady

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


UTC = datetime.timezone.utc
LOG = logging.getLogger(__name__)


class ArryvedMenuParser(BaseTapListProvider):
    """Parser for Arrvyed embedded menus"""

    provider_name = "arryved_embedded_menu"
    BASE_URL = "https://menu.arryved.com/arryvedView?locationId={}&menuId={}"
    URL = "https://menu.arryved.com/preauthAction/getMenu"

    def __init__(
        self,
        manufacturer: Manufacturer = None,
        location_id: str = None,
        menu_id: str = None,
        serving_sizes: list[str] = None,
    ):
        self.location_id = location_id
        self.menu_id = menu_id
        self.manufacturer = manufacturer
        self.serving_sizes = set(serving_sizes) if serving_sizes else set()

    def handle_venue(self, venue: Venue) -> datetime.datetime:
        self.location_id = venue.api_configuration.arryved_location_id
        self.menu_id = venue.api_configuration.arryved_menu_id
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
        last_updated = datetime.datetime(1970, 1, 1, 0, tzinfo=UTC)
        prices = []
        serving_sizes = {i.volume_oz: i for i in ServingSize.objects.all()}
        tap_number = 1
        for beer in json_data["beers"]:
            tap = taps.get(tap_number, Tap(tap_number=tap_number, venue=venue))
            existing_beer_pk = tap.beer_id
            beer_created = False
            try:
                tap.beer = manufacturer_beers[beer["name"]]
            except KeyError:
                try:
                    tap.beer = Beer.objects.get(
                        manufacturer=self.manufacturer,
                        alternate_names__contains=[beer["name"]],
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
            if tap.beer.id != existing_beer_pk:
                tap.time_added = beer["last_updated"]
            if beer["ibu"]:
                tap.beer.ibu = beer["ibu"]
            if beer["abv"]:
                tap.beer.abv = beer["abv"]
            tap.time_updated = beer["last_updated"]
            LOG.debug("Saving tap %s: %s", tap.tap_number, tap.beer)
            tap.save()
            if beer["last_updated"] > last_updated:
                last_updated = beer["last_updated"]
            tap_number += 1
        delete_result = Tap.objects.filter(
            venue=venue,
            tap_number__gte=tap_number,
        ).delete()
        LOG.debug("Deleted %s extra taps", delete_result[0])
        BeerPrice.objects.bulk_create(prices)
        self.check_timestamp = last_updated
        return last_updated

    def process_serving_sizes(
        self,
        beer: Beer,
        venue: Venue,
        pricing_data: list[dict],
        serving_sizes: dict[Decimal, ServingSize],
    ) -> list[BeerPrice]:
        result = []
        for size_dict in pricing_data:
            LOG.debug("size dict: %s", size_dict)
            if size_dict["size"]["short_code"] not in self.serving_sizes:
                LOG.debug("Skipping serving size %s", size_dict["size"]["short_code"])
                continue
            capacity = Decimal(size_dict["size"]["serving_size"])
            price = size_dict["price"]
            try:
                serving_size = serving_sizes[Decimal(size_dict["size"]["serving_size"])]
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
                "venueIds": [],
                "itemTypes": [],
                "publicConfigType": "WEBSITE_EMBED",
                "menuId": self.menu_id,
            },
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "referer": self.BASE_URL.format(self.location_id, self.menu_id),
            },
        )
        response.raise_for_status()
        return response.json()

    def parse_json(self, json_data: dict[str, Any]):
        payload = json_data["payload"]
        sizes = self.parse_sizes(payload)
        item_types = self.parse_item_types(payload)
        last_updated = datetime.datetime.fromtimestamp(
            payload["lastUpdatedAt"] / 1000, UTC
        )
        beers = self.parse_items(payload, sizes)
        return {
            "beers": beers,
            "last_updated": last_updated,
            "item_types": item_types,
        }

    def parse_sizes(self, payload: dict[str, dict]) -> dict[str, str | int | float]:
        """Parse serving sizes"""
        result = {
            short_code: {
                "serving_size": data["quantityMicros"] / 1e6,
                "name": data["display"],
                "short_code": short_code,
            }
            for short_code, data in payload["sizes"].items()
            if not data["retired"]
        }
        return result

    def parse_item_types(self, payload: dict[str, dict]) -> dict[str, str]:
        return {
            short_code: data["name"].title()
            for short_code, data in payload["itemTypes"].items()
            if not data["retired"]
        }

    def parse_item_available_sizes(
        self, payload: dict[str, dict]
    ) -> dict[str, list[dict[str, str | int | float]]]:
        sizes = self.parse_sizes(payload)
        result = defaultdict(list)
        for line in payload["activeItemSizes"]:
            key, short_code = line.split(":::")
            result[key].append(sizes[short_code])
        return result

    def parse_items(
        self,
        payload: dict[str, dict],
        sizes: dict[str, str | int | float],
    ) -> list[dict[str, str | int | float]]:
        result = []
        for item in payload["items"]:
            result.append(
                {
                    "pk": item["id"],
                    "name": item["displayDetails"]["name"],
                    "alternate_name": item["displayDetails"]["shortName"],
                    "serving_sizes": [
                        {
                            "size": sizes[cost["size"]],
                            "price": cost["cost"]["micros"] / 1e6,
                        }
                        for cost in item["itemCosts"]
                        if cost["state"] == "ACTIVE"
                    ],
                    "abv": self.get_abv(item["attributes"]),
                    "ibu": self.get_ibu(item["attributes"]),
                    "last_updated": datetime.datetime.fromtimestamp(
                        item["lastUpdateTime"] / 1000, UTC
                    ),
                }
            )
        return result

    def get_ibu(self, attributes: list[dict[str, str]]) -> int | None:
        try:
            value = [i["value"] for i in attributes if i["type"] == "IBU"][0]
            return int(value)
        except IndexError:
            return None
        except (TypeError, ValueError) as exc:
            LOG.warning("Unable to parse IBU value in %s: %s", attributes, exc)
            return None

    def get_abv(self, attributes: list[dict[str, str]]) -> Decimal | None:
        try:
            value = [i["value"] for i in attributes if i["type"] == "ABV"][0].replace(
                "%", ""
            )
            return Decimal(value)
        except IndexError:
            return None
        except (TypeError, ValueError) as exc:
            LOG.warning("Unable to parse ABV value in %s: %s", attributes, exc)
            return None
