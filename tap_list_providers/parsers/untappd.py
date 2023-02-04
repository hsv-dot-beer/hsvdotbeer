"""Parse data from untappd"""
import argparse
import datetime
from collections import Counter
from decimal import Decimal, InvalidOperation
from pprint import PrettyPrinter
import logging
import os
import re

import dateutil.parser
from dateutil.relativedelta import relativedelta
import requests
from bs4 import BeautifulSoup
import configurations
from django.utils.timezone import now
from django.core.exceptions import ImproperlyConfigured, AppRegistryNotReady
from django.db.models import Q

# boilerplate code necessary for launching outside manage.py
try:
    from ..base import BaseTapListProvider
except (ImproperlyConfigured, AppRegistryNotReady):
    os.environ["DJANGO_SETTINGS_MODULE"] = "hsv_dot_beer.config"
    os.environ.setdefault("DJANGO_CONFIGURATION", "Local")
    configurations.setup()
    from ..base import BaseTapListProvider

from beers.models import Style
from taps.models import Tap


UTC = datetime.timezone.utc
LOG = logging.getLogger(__name__)
ABV_REGEX = re.compile(r"\d{1,2}(\.\d{1,3})?")
IBU_REGEX = re.compile(r"\d{1,3}(\.\d{1,3})?")
# we want to match 6 pack, 12-pack, 24-Pack, 6 Pack, etc
X_PACK_REGEX = re.compile(r"\d*(\s|-)*(P|p)ack")


class UntappdParser(BaseTapListProvider):
    URL = "https://business.untappd.com/locations/{}/themes/{}/js"
    SEARCH = 'container.innerHTML = "'
    provider_name = "untappd"

    def __init__(self, location=None, theme=None, cats=None):
        self.location_url = None
        if location and theme:
            self.location_url = self.URL.format(location, theme)
        LOG.debug("categories: %s", cats)
        self.categories = [i.casefold() for i in cats] if cats else []
        self.soup = None
        self.taplists = []
        self.venue_name = ""
        super().__init__()

    def fetch_data(self):
        if not self.location_url:
            raise ValueError("You must configure the location URL")
        data = requests.get(self.location_url).text
        return data

    def handle_venue(self, venue):
        self.categories = [
            i.casefold() for i in venue.api_configuration.untappd_categories
        ]
        LOG.debug("Categories: %s", self.categories)
        self.venue_name = venue.name
        self.location_url = self.URL.format(
            venue.api_configuration.untappd_location,
            venue.api_configuration.untappd_theme,
        )
        data = self.fetch_data()
        self.parse_html_and_js(data)

        taps = {tap.tap_number: tap for tap in venue.taps.all()}
        manufacturers = {}
        tap_list = self.taps()
        use_sequential_taps = any(
            tap_info["tap_number"] is None for tap_info in tap_list
        )
        tap_counts = Counter(tap_info["tap_number"] for tap_info in tap_list)
        if any(
            tap_count > 1
            for tap_number, tap_count in tap_counts.items()
            if tap_number is not None
        ):
            LOG.warning("Found duplicate tap numbers. Omitting them")
            use_sequential_taps = True

        LOG.debug("use sequential taps? %s", use_sequential_taps)
        if not use_sequential_taps:
            populated_taps: list[int] = [
                tap_info["tap_number"] for tap_info in tap_list
            ]
        else:
            populated_taps = list(range(1, len(tap_list) + 1))

        LOG.debug("populated taps: %s", populated_taps)
        cleared = (
            Tap.objects.filter(
                venue=venue,
            )
            .exclude(
                tap_number__in=populated_taps,
            )
            .delete()[1]
            .get("taps.Tap", 0)
        )
        if cleared:
            LOG.info(
                "Cleared %s now unused taps (not in %s)",
                cleared,
                sorted(populated_taps),
            )
        latest_timestamp = datetime.datetime(1970, 1, 1, 12, tzinfo=UTC)
        for index, tap_info in enumerate(tap_list):
            # 1. get the tap
            # if the venue doesn't give tap numbers, just use a 1-based
            # counter
            if use_sequential_taps:
                tap_number = index + 1
            else:
                tap_number = tap_info["tap_number"]
            try:
                tap = taps[tap_number]
            except KeyError:
                tap = Tap(venue=venue, tap_number=tap_number)
            if tap_info["added"]:
                tap.time_added = dateutil.parser.parse(tap_info["added"])
                if tap.time_added > latest_timestamp:
                    LOG.debug(
                        "latest timestamp updated to %s (added)",
                        tap.time_updated,
                    )
                    latest_timestamp = tap.time_added
            if tap_info["updated"]:
                tap.time_updated = dateutil.parser.parse(tap_info["updated"])
                if tap.time_updated > latest_timestamp:
                    LOG.debug(
                        "latest timestamp updated to %s (updated)",
                        tap.time_updated,
                    )
                    latest_timestamp = tap.time_updated
            # 2. parse the manufacturer
            try:
                manufacturer = manufacturers[tap_info["manufacturer"]["name"]]
            except KeyError:
                location = tap_info["manufacturer"]["location"]
                defaults = {
                    "untappd_url": tap_info["manufacturer"]["untappd_url"],
                }
                if location:
                    defaults["location"] = location
                manufacturer = self.get_manufacturer(
                    tap_info["manufacturer"]["name"],
                    **defaults,
                )
                manufacturers[manufacturer.name] = manufacturer
            # 3. get the beer, creating if necessary
            beer_name = tap_info["beer"].pop("name")
            beer = self.get_beer(
                beer_name,
                manufacturer,
                venue=venue,
                pricing=tap_info["pricing"],
                **tap_info["beer"],
            )
            # 4. assign the beer to the tap
            tap.beer = beer
            tap.save()
        if latest_timestamp == datetime.datetime(1970, 1, 1, 12, tzinfo=UTC):
            return None
        return latest_timestamp

    def parse_html_and_js(self, data):
        # Pull the relevant HTML from the JS.
        start_idx = data.find(self.SEARCH)
        end_idx = data.find(";\n\n")
        html = data[(start_idx + len(self.SEARCH)) : end_idx]

        # Unescape the HTML
        html = html.replace("\\n", "")
        html = html.replace('\\"', '"')
        html = html.replace("\\/", "/")
        html = html.replace("\\'", "'")

        self.soup = BeautifulSoup(html, "lxml")

        info_elements = self.soup.find_all("div", {"class": "section"})

        self.taplists = []

        for element in info_elements:
            header = element.find("div", {"class": "section-name"})
            if header is None:
                header = element.find("div", {"class": "section-heading"})
            text = header.text
            if text.casefold().strip() in self.categories:
                LOG.debug("Adding tap list %s", text)
                self.taplists.append(element)
            else:
                LOG.debug("Ignoring tap list %s", text)

    def parse_style(self, style):
        if "-" in style:
            split_names = [i.strip() for i in style.split(" - ")]
            cat = None
            name = None
            if len(split_names) == 2:
                cat, name = split_names
            elif len(split_names) > 2:
                # use the last two
                cat, name = split_names[-2:]
            else:
                # we have bad padding
                # pad it and retry
                return self.parse_style(style.replace("-", " - "))
            # attempt 1: has the style been moderated already?
            try:
                return Style.objects.get(alternate_names__contains=[style])
            except Style.DoesNotExist:
                # don't care
                pass
            # attempt 2: change IPA - Belgian to Belgian IPA
            try:
                candidate = f"{name} {cat}"
                return (
                    Style.objects.filter(
                        Q(name__iexact=candidate)
                        | Q(alternate_names__contains=[candidate])
                    )
                    .distinct()
                    .get()
                )
            except Style.DoesNotExist:
                # don't care
                pass
            except Style.MultipleObjectsReturned:
                # we have two different options
                # pick the exact match and move on
                LOG.error("Two different matches for style %s", candidate)
                return Style.objects.get(name__iexact=candidate)
            # attempt 3: try name by itself
            # (e.g. Ciders and Meads - English Cider -> English Cider)
            try:
                return (
                    Style.objects.filter(
                        Q(name__iexact=name) | Q(alternate_names__contains=[name])
                    )
                    .distinct()
                    .get()
                )
            except Style.MultipleObjectsReturned:
                LOG.error("Two different matches for name %s", name)
                return Style.objects.get(name__iexact=name)
            except Style.DoesNotExist:
                # womp womp
                return Style.objects.get_or_create(name=f"{cat} - {name}")[0]

        cat = None
        name = style.strip()
        return Style.objects.get_or_create(name=style)[0]

    def parse_size(self, size: str) -> int:
        custom_sizes = {
            "1/6 barrel": 660,
            "1/4 barrel": 996,
            "1/2 barrel": 1980,
            # Chattahoochee uses 6 oz tasters; we can revisit if needed later
            "flight": 6,
            "half pint": 8,
            "pint": 16,
            "half liter": 16.9,
            ".5 liter": 16.9,
            # going to round these to pints (both at Common Bond)
            "draft": 16,
            "nitro": 16,
        }
        if X_PACK_REGEX.search(size.strip()):
            raise InvalidSize(size.strip())
        try:
            return custom_sizes[size.strip().casefold()]
        except KeyError as exc:
            # must use EAFP because Python will try to evaluate this in the case of
            # one of the custom sizes above
            if "oz" in size.casefold():
                return Decimal(size.casefold().split("oz")[0].strip())
            if "liter" in size.casefold():
                return Decimal(
                    # yes, I know this conversion factor is over-precise since we're
                    # rounding to the nearest 0.1 oz anyway.
                    float(size.casefold().split("liter")[0].strip())
                    * 33.8140226
                )
            raise ValueError(f"Unknown serving size {size!r}") from exc

    def parse_price(self, price: str) -> float:
        price = price.replace("$", "").strip().replace("\\", "")
        return float(price)

    def parse_pricing(self, entry):
        pricing = []

        price_div = entry.find("div", {"class": "with-price"})
        if price_div:
            for row in price_div.find_all("div", {"class": "container-row"}):
                try:
                    size = row.find("span", {"class": "type"}).text
                    price = row.find("span", {"class": "price"}).text
                except AttributeError:
                    LOG.debug("No price entry found for row %s", row)
                    continue
                try:
                    price = {
                        "volume_oz": Decimal(self.parse_size(size)),
                        "name": size,
                        "price": self.parse_price(price),
                    }
                except (InvalidOperation, InvalidSize):
                    LOG.warning("skipping invalid size %s", size.strip())
                    continue
                price["per_ounce"] = Decimal(price["price"]) / price["volume_oz"]
                pricing.append(price)
        return pricing

    def parse_tap(self, entry):
        beer_name_p = entry.find("p", {"class": "beer-name"})
        if beer_name_p is None:
            return self.parse_item_tap(entry)
        beer_info = beer_name_p.text
        LOG.debug("parsing beer %s", beer_info)
        tap_num = entry.find(
            "span",
            {"class": "tap-number-hideable"},
        ).text.strip()
        beer_link = entry.find(
            "div",
            {"class": "label-image-hideable beer-label pull-left"},
        )
        beer_link_tag = beer_link.find("a")
        beer_image = beer_link.find("img").attrs["src"]
        if beer_link_tag:
            url = beer_link_tag.attrs["href"]
        else:
            url = None

        beer_style = entry.find("span", {"class": "beer-style"}).text.strip()
        brewery_span = entry.find("span", {"class": "brewery"})
        brewery = brewery_span.text.strip()
        brewery_url = brewery_span.find("a").attrs["href"]

        location_span = entry.find("span", {"class": "location"})
        if location_span:
            loc = location_span.text
        else:
            loc = ""

        beer_info = beer_info.replace(tap_num, "")
        beer_info = beer_info.replace(beer_style, "")
        beer_info = beer_info.strip()
        if not beer_info or beer_info == brewery:
            beer_info = f"{brewery} {beer_style}"

        tap_dict = {
            "beer": {
                "name": beer_info,
                "untappd_url": url,
                "style": self.parse_style(beer_style),
                "logo_url": beer_image,
            },
            "manufacturer": {
                "name": brewery,
                "location": loc,
                "untappd_url": brewery_url,
            },
            "pricing": self.parse_pricing(entry),
            "added": None,
            "updated": None,
            "tap_number": int(tap_num.replace(".", "")) if tap_num else None,
        }

        abv_span = entry.find("span", {"class": "abv"})
        if abv_span:
            abv = abv_span.text
            abv = abv.replace("ABV", "")
            abv = float(abv.replace("%", ""))
        else:
            abv = None

        tap_dict["beer"]["abv"] = abv

        ibu = entry.find("span", {"class": "ibu"})
        if ibu:
            ibu = ibu.text.replace("IBU", "")
            ibu = float(ibu)
            tap_dict["beer"]["ibu"] = ibu

        return tap_dict

    def parse_item_tap(self, entry):
        beer_name_span = entry.find("a", {"class": "item-title-color"})
        beer_info = beer_name_span.text
        LOG.debug("parsing beer %s", beer_info)
        if tap_span := (
            entry.find("span", {"class": "tap-number-hideable"})
            or entry.find("span", {"class": "item-tap-number"})
        ):
            tap_num: str = tap_span.text.strip()
        else:
            tap_num = ""
        beer_link = entry.find(
            "div",
            {"class": "label-image-hideable item-label pull-left"},
        )
        url = None
        beer_image = None
        if beer_link:
            beer_link_tag = beer_link.find("a")
            beer_image = beer_link.find("img").attrs["src"]
            if beer_link_tag:
                url = beer_link_tag.attrs["href"]

        beer_style = (
            entry.find(
                "span",
                {"class": "item-style"},
            )
            .text.replace("•", "")
            .replace("\xa0", "")
            .strip()
        )
        if brewery_span := entry.find("span", {"class": "brewery"}):
            brewery = brewery_span.text.strip()

            brewery_url = None
            if brewery_url_a := brewery_span.find("a"):
                brewery_url = brewery_url_a.attrs["href"]
        else:
            brewery = self.venue_name
            brewery_url = ""

        location_span = entry.find("span", {"class": "location"})
        if location_span:
            loc = location_span.text
        else:
            loc = ""

        beer_info = beer_info.replace(tap_num, "")
        beer_info = beer_info.replace(beer_style, "")
        beer_info = beer_info.strip()
        if not beer_info or beer_info == brewery:
            beer_info = f"{brewery} {beer_style}"

        t = {
            "beer": {
                "name": beer_info,
                "untappd_url": url,
                "style": self.parse_style(beer_style),
                "logo_url": beer_image,
            },
            "manufacturer": {
                "name": brewery,
                "location": loc,
                "untappd_url": brewery_url,
            },
            "pricing": self.parse_pricing(entry),
            "added": None,
            "updated": None,
            "tap_number": int(tap_num.replace(".", "")) if tap_num else None,
        }

        abv_span = entry.find("span", {"class": "abv"})
        if abv_span:
            abv = abv_span.text
            match = ABV_REGEX.search(abv)
            try:
                abv = float(match[0])
            except (TypeError, IndexError):
                LOG.warning("Unable to parse ABV %r", abv_span.text)
                abv = None
        else:
            abv = None

        t["beer"]["abv"] = abv

        ibu = entry.find("span", {"class": "ibu"})
        if ibu:
            match = IBU_REGEX.search(ibu.text)
            try:
                ibu = float(match[0])
            except (TypeError, IndexError):
                LOG.warning("Unable to parse IBU %r", ibu.text)
                ibu = None

            t["beer"]["ibu"] = ibu

        return t

    def taps(self):
        ret = []
        for taplist in self.taplists:
            LOG.debug("Opening tap list")
            entries = taplist.find_all("div", {"class": "menu-item"})
            LOG.debug("Found %s entries", len(entries))
            updated = None
            menus = self.soup.find_all("div", {"class": "menu-info"})
            for menu in menus:
                if time_element := menu.find("time"):
                    updated_str: str = time_element.text.strip()
                    LOG.debug("updated time: %s", updated_str)
                    if updated_str.endswith("ST") or updated_str.endswith("DT"):
                        # it isn't in UTC. Grr.
                        # for now, just support CONUS time zones
                        tzinfos = {
                            "EST": -5 * 3600,
                            "EDT": -4 * 3600,
                            "CST": -6 * 3600,
                            "CDT": -5 * 3600,
                            "MST": -7 * 3600,
                            "MDT": -6 * 3600,
                            "PST": -8 * 3600,
                            "PDT": -7 * 3600,
                        }
                        list_updated = dateutil.parser.parse(
                            updated_str,
                            tzinfos=tzinfos,
                        )
                    else:
                        list_updated = dateutil.parser.parse(updated_str)
                    # HACK: if the time is in the future, rewind by a year
                    if list_updated > now():
                        list_updated = list_updated - relativedelta(years=1)
                    if updated is None or list_updated > updated:
                        LOG.debug("setting tap list updated to %s", list_updated)
                        updated = list_updated

            for entry in entries:
                tap_info = self.parse_tap(entry)
                tap_info["updated"] = updated.isoformat()
                LOG.debug("Set timestamp to %s", updated)
                ret.append(tap_info)
        return ret


def main():
    logging.basicConfig(level=logging.DEBUG)

    locations = {
        "dsb": ("3884", "11913", ["Tap List"]),
        "cpp": ("18351", "69229", ["On Tap"]),
        "yh": ("5949", "20074", ["YEAR-ROUND", "SEASONALS", "Beer"]),
        "mm": ("8588", "30573", ["Favorites", "Seasonals", "Exclusives"]),
        "vonbrewski": (
            "19449",
            "73621",
            ["Left Wall", "Right Wall", "Trailer", "Back Wall", "On Deck"],
        ),
        "goat": ("4632", "14806", ["Goat Island Brewing"]),
        "chatt": ("1827", "3788", ["Menu"]),
        "isb": (
            "33847",
            "130917",
            [
                "IPAs",
                "Saisons",
                "Fruity & Fresh",
                "The Dark Side",
                "Pale Ales",
                "Reds, Ambers, and Browns",
                "English Styles",
                "Lagers",
                "Wheats",
                "German Styles",
                "Ciders",
                "Sours",
            ],
        ),
    }

    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", action="store_true")
    parser.add_argument("--print-logo-url", action="store_true")
    parser.add_argument("location")
    args = parser.parse_args()

    untappd_parser = UntappdParser(*locations[args.location])
    data = untappd_parser.fetch_data()
    untappd_parser.parse_html_and_js(data)

    if args.dump:
        print(untappd_parser.soup.prettify())

    for tap in untappd_parser.taps():
        PrettyPrinter(indent=4).pprint(tap)


class InvalidSize(Exception):
    """The tap list contains a portion size that we can't parse"""


if __name__ == "__main__":
    main()
