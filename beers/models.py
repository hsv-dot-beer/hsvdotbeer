import logging
from typing import Iterable

from django.contrib.postgres.fields import CITextField, ArrayField
from django.db import models, transaction
from django.db.utils import IntegrityError
from django.utils.timezone import now
from django.db.models import JSONField

from taps.models import Tap
from .utils import render_srm


LOG = logging.getLogger(__name__)


class Style(models.Model):
    name = CITextField(unique=True)
    default_color = models.CharField(
        "HTML color (in hex) to use if the beer has no known color",
        max_length=9,  # #00112233 -> RGBA
        blank=True,
    )
    alternate_names = ArrayField(CITextField(), default=list)

    def merge_from(self, other_styles: Iterable["Style"]):
        with transaction.atomic():
            for style in other_styles:
                if style.id == self.id:
                    continue
                self.alternate_names.append(style.name)
                self.alternate_names.extend(style.alternate_names)
                style.beers.all().update(style=self)
                style.delete()
            self.alternate_names = sorted(set(self.alternate_names))
            if duplicates := list(
                Style.objects.filter(
                    models.Q(alternate_names__contained_by=self.alternate_names)
                    | models.Q(name__in=self.alternate_names)
                ).exclude(id=self.id)
            ):
                raise ValueError(
                    f"These styles share duplicate alternate names: {duplicates}"
                )

            self.save()

    def __str__(self):  # pylint: disable=invalid-str-returned
        return self.name


class Manufacturer(models.Model):
    name = CITextField()
    url = models.URLField(blank=True)
    location = models.CharField(blank=True, max_length=250)
    logo_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    instagram_handle = models.CharField(max_length=50, blank=True)
    untappd_url = models.URLField(blank=True, null=True)
    automatic_updates_blocked = models.BooleanField(null=True, default=False)
    taphunter_url = models.URLField(blank=True, null=True)
    taplist_io_pk = models.PositiveIntegerField(blank=True, null=True)
    time_first_seen = models.DateTimeField(blank=True, null=True, default=now)
    beermenus_slug = models.CharField(max_length=250, blank=True, null=True)
    alternate_names = ArrayField(CITextField(), default=list)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name"], name="unique_mfg_name"),
            models.UniqueConstraint(
                fields=["taplist_io_pk"], name="unique_mfg_taplist_io_pk"
            ),
            models.UniqueConstraint(
                fields=["taphunter_url"], name="unique_mfg_taphunter_url"
            ),
            models.UniqueConstraint(
                fields=["untappd_url"], name="unique_mfg_untappd_url"
            ),
            models.UniqueConstraint(
                fields=["beermenus_slug"], name="unique_mfg_beermenus_slug"
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.beermenus_slug:
            self.beermenus_slug = None
        if not self.taphunter_url:
            self.taphunter_url = None
        if not self.untappd_url:
            self.untappd_url = None
        return super().save(*args, **kwargs)

    def merge_from(self, other: "Manufacturer"):
        """Merge the data from other into self"""
        LOG.info("merging %s into %s", other, self)
        with transaction.atomic():
            other_beers: list[Beer] = list(other.beers.all())
            my_beers: dict[str, Beer] = {i.name.casefold(): i for i in self.beers.all()}
            for beer in other_beers:
                beer.manufacturer = self
                if beer.name.casefold() in my_beers:
                    # we have a duplicate beer. Merge those two first.
                    # merge_from takes care of saving my_beer and deleting
                    # beer
                    # keep the one that was already present
                    my_beer = my_beers[beer.name.casefold()]
                    my_beer.merge_from(beer)
                else:
                    # good
                    beer.save()
            self.alternate_names.extend(other.alternate_names)
            self.alternate_names.append(other.name)
            self.alternate_names = sorted(set(self.alternate_names))
            excluded_fields = {
                "name",
                "automatic_updates_blocked",
                "id",
                "time_first_seen",
                "alternate_names",
            }
            for field in self._meta.fields:
                field_name = field.name
                if field_name in excluded_fields:
                    continue
                other_value = getattr(other, field_name)
                if getattr(self, field_name) or not other_value:
                    # don't overwrite data that's already there
                    # or isn't set in the other one
                    continue
                setattr(self, field_name, other_value)
            self.automatic_updates_blocked = True
            other.delete()
            if other.time_first_seen:
                if (
                    not self.time_first_seen
                    or self.time_first_seen > other.time_first_seen
                ):
                    self.time_first_seen = other.time_first_seen
            self.save()

    def __str__(self):  # pylint: disable=invalid-str-returned
        return self.name


class Beer(models.Model):
    name = CITextField()
    style = models.ForeignKey(
        Style,
        models.DO_NOTHING,
        related_name="beers",
        blank=True,
        null=True,
    )
    manufacturer = models.ForeignKey(
        Manufacturer,
        models.CASCADE,
        related_name="beers",
    )
    in_production = models.BooleanField(default=True)
    abv = models.DecimalField(
        "Alcohol content (% by volume)",
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
    )
    ibu = models.PositiveSmallIntegerField(
        "Bitterness (International Bitterness Units)",
        blank=True,
        null=True,
    )
    color_srm = models.DecimalField(
        "Color (Standard Reference Method)",
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
    )
    untappd_url = models.URLField("Untappd URL (if known)", blank=True, null=True)
    beer_advocate_url = models.URLField(
        "BeerAdvocate URL (if known)", null=True, blank=True
    )
    rate_beer_url = models.URLField("RateBeer URL (if known)", blank=True, null=True)
    logo_url = models.URLField("Beer logo URL (if known)", blank=True, null=True)
    color_html = models.CharField(
        "HTML Color (in hex)",
        max_length=9,
        blank=True,  # #00112233 -> RGBA
    )
    api_vendor_style = models.CharField(
        "API vendor-provided style (hidden from API)",
        max_length=100,
        blank=True,
    )
    manufacturer_url = models.URLField(
        "Link to the beer on the manufacturer's website",
        blank=True,
        null=True,
    )
    automatic_updates_blocked = models.BooleanField(null=True, default=False)
    taphunter_url = models.URLField("TapHunter URL (if known)", blank=True, null=True)
    stem_and_stein_pk = models.PositiveIntegerField(blank=True, null=True)
    taplist_io_pk = models.PositiveIntegerField(blank=True, null=True)
    time_first_seen = models.DateTimeField(blank=True, null=True, default=now)
    tweeted_about = models.BooleanField(default=False)
    beermenus_slug = models.CharField(max_length=250, blank=True, null=True)
    alternate_names = ArrayField(CITextField(), default=list)

    class Meta:
        indexes = [
            models.Index(fields=["tweeted_about"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(abv__gte=0, abv__lte=100) | models.Q(abv__isnull=True),
                name="abv_positive",
            ),
            models.CheckConstraint(
                check=models.Q(ibu__lte=1000) | models.Q(ibu__isnull=True),
                name="ibu_not_unreal",
            ),
            models.CheckConstraint(
                check=models.Q(color_srm__lte=500, color_srm__gte=1)
                | models.Q(color_srm__isnull=True),
                name="srm_not_unrealistic",
            ),
            models.UniqueConstraint(
                fields=["beermenus_slug"],
                name="unique_beermenus_slug",
            ),
            models.UniqueConstraint(
                fields=["taplist_io_pk"],
                name="unique_taplist_io_pk",
            ),
            models.UniqueConstraint(
                fields=["stem_and_stein_pk"],
                name="unique_stem_and_stein_pk",
            ),
            models.UniqueConstraint(
                fields=["taphunter_url"],
                name="unique_taphunter_url",
            ),
            models.UniqueConstraint(
                fields=["manufacturer_url"],
                name="unique_manufacturer_url",
            ),
            models.UniqueConstraint(
                fields=["rate_beer_url"],
                name="unique_rate_beer_url",
            ),
            models.UniqueConstraint(
                fields=["untappd_url"],
                name="unique_untappd_url",
            ),
            models.UniqueConstraint(
                fields=["beer_advocate_url"],
                name="unique_beer_advocate_url",
            ),
            models.UniqueConstraint(
                fields=["name", "manufacturer"],
                name="unique_beer_per_manufacturer",
            ),
        ]

    def save(self, *args, **kwargs):
        # force empty IDs to null to avoid running afoul of unique constraints
        if not self.untappd_url:
            self.untappd_url = None
        if not self.beer_advocate_url:
            self.beer_advocate_url = None
        if not self.rate_beer_url:
            self.rate_beer_url = None
        if not self.manufacturer_url:
            self.manufacturer_url = None
        if not self.taphunter_url:
            self.taphunter_url = None
        if not self.beermenus_slug:
            self.beermenus_slug = None
        return super().save(*args, **kwargs)

    def __str__(self):  # pylint: disable=invalid-str-returned
        return self.name

    def render_srm(self):
        """Convert beer color in SRM into an HTML hex color"""
        if self.color_html:
            return self.color_html
        return render_srm(self.color_srm)

    def merge_from(self, other: "Beer"):
        LOG.info("merging %s into %s", other, self)
        with transaction.atomic():
            Tap.objects.filter(beer=other).update(beer=self)
            self.alternate_names.extend(other.alternate_names)
            try:
                with transaction.atomic():
                    BeerPrice.objects.filter(beer=other).update(beer=self)
            except IntegrityError:
                LOG.warning("Duplicate prices detected for %s", self)
                prices_updated = (
                    BeerPrice.objects.filter(beer=other)
                    .exclude(
                        venue__in=models.Subquery(
                            BeerPrice.objects.filter(beer=self).values("venue")
                        ),
                    )
                    .update(beer=self)
                )
                prices_deleted = BeerPrice.objects.filter(beer=other).delete()
                LOG.info(
                    "Updated %s prices and deleted %s prices",
                    prices_updated,
                    prices_deleted,
                )
            excluded_fields = {
                "name",
                "in_production",
                "automatic_updates_blocked",
                "manufacturer",
                "id",
                "time_first_seen",
                "alternate_names",
            }
            for field in self._meta.fields:
                field_name = field.name
                if field_name in excluded_fields:
                    continue
                other_value = getattr(other, field_name)
                if getattr(self, field_name) or not other_value:
                    # don't overwrite data that's already there
                    # or isn't set in the other one
                    continue
                setattr(self, field_name, other_value)
            self.automatic_updates_blocked = True
            if other.name != self.name:
                # this will only not happen if manufacturers aren't the same
                self.alternate_names.append(other.name)
            self.alternate_names = sorted(set(self.alternate_names))
            if other.time_first_seen:
                if (
                    not self.time_first_seen
                    or self.time_first_seen > other.time_first_seen
                ):
                    self.time_first_seen = other.time_first_seen
            other.delete()
            self.save()


class ServingSize(models.Model):
    name = models.CharField(max_length=50, unique=True)
    # max 9999.9 oz
    volume_oz = models.DecimalField(
        unique=True,
        null=True,
        blank=True,
        max_digits=5,
        decimal_places=1,
    )

    def __str__(self):
        return self.name


class BeerPrice(models.Model):
    beer = models.ForeignKey(Beer, models.CASCADE, related_name="prices")
    venue = models.ForeignKey(
        "venues.Venue",
        models.CASCADE,
        related_name="beer_prices",
    )
    serving_size = models.ForeignKey(
        ServingSize,
        models.DO_NOTHING,
        related_name="beer_prices",
    )
    # max $999.99
    price = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )

    def __str__(self):
        return f"${self.price} for {self.beer_id} at {self.venue_id}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["beer", "venue", "serving_size"],
                name="beer_venue_servingsize",
            ),
        ]


class UntappdMetadata(models.Model):
    json_data = JSONField()
    timestamp = models.DateTimeField(auto_now=True)
    beer = models.OneToOneField(
        Beer,
        models.CASCADE,
        related_name="untappd_metadata",
    )
