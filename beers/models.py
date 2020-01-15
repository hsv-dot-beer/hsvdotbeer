import logging

from django.contrib.postgres.fields import JSONField, CITextField
from django.db import models, transaction
from django.db.utils import IntegrityError
from django.utils.timezone import now

from taps.models import Tap
from .utils import render_srm

LOG = logging.getLogger(__name__)


class Style(models.Model):
    name = CITextField(unique=True)
    default_color = models.CharField(
        'HTML color (in hex) to use if the beer has no known color',
        max_length=9,  # #00112233 -> RGBA
        blank=True,
    )

    def merge_from(self, other_styles):
        alt_names = []
        with transaction.atomic():
            for style in other_styles:
                if style.id == self.id:
                    continue
                alt_names.append(style.name)
                style.beers.all().update(style=self)
                style.alternate_names.all().update(style=self)
                style.delete()
            try:
                # need the second transaction so we can run a query in the
                # event this fails. Because we're doing a raise in the except
                # block, the outer transaction will still be aborted in case
                # of failure.
                with transaction.atomic():
                    StyleAlternateName.objects.bulk_create([
                        StyleAlternateName(
                            name=name,
                            style=self,
                        ) for name in alt_names
                    ])
            except IntegrityError:
                existing_names = [
                    i.name for i in StyleAlternateName.objects.filter(
                        name__in=alt_names,
                    ).exclude(
                        style=self,
                    )
                ]
                raise ValueError(
                    'These alternate names already exist: '
                    f'{", ".join(existing_names)}'
                )

    def __str__(self):
        return self.name


class StyleAlternateName(models.Model):
    name = CITextField(unique=True)
    style = models.ForeignKey(
        Style, models.CASCADE, related_name='alternate_names')

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    name = CITextField(unique=True)
    url = models.URLField(blank=True)
    location = models.CharField(blank=True, max_length=50)
    logo_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    instagram_handle = models.CharField(max_length=50, blank=True)
    untappd_url = models.URLField(blank=True, unique=True, null=True)
    automatic_updates_blocked = models.NullBooleanField(default=False)
    taphunter_url = models.URLField(blank=True, null=True, unique=True)
    taplist_io_pk = models.PositiveIntegerField(
        blank=True, null=True, unique=True,
    )
    time_first_seen = models.DateTimeField(blank=True, null=True, default=now)
    beermenus_slug = models.CharField(
        max_length=250, blank=True, null=True, unique=True,
    )

    def save(self, *args, **kwargs):
        if not self.beermenus_slug:
            self.beermenus_slug = None
        if not self.taphunter_url:
            self.taphunter_url = None
        if not self.untappd_url:
            self.untappd_url = None
        return super().save(*args, **kwargs)

    def merge_from(self, other):
        LOG.info('merging %s into %s', other, self)
        with transaction.atomic():
            other_beers = list(other.beers.all())
            my_beers = {i.name.casefold(): i for i in self.beers.all()}
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

            ManufacturerAlternateName.objects.filter(
                manufacturer=other,
            ).update(manufacturer=self)
            excluded_fields = {
                'name', 'automatic_updates_blocked', 'id', 'time_first_seen',
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
            ManufacturerAlternateName.objects.update_or_create(
                name=other.name,
                manufacturer=self,
            )
            other.delete()
            if other.time_first_seen:
                if not self.time_first_seen or \
                        self.time_first_seen > other.time_first_seen:
                    self.time_first_seen = other.time_first_seen
            self.save()

    def __str__(self):
        return self.name


class Beer(models.Model):
    name = CITextField()
    style = models.ForeignKey(
        Style, models.DO_NOTHING, related_name='beers',
        blank=True, null=True,
    )
    manufacturer = models.ForeignKey(
        Manufacturer, models.CASCADE, related_name='beers',
    )
    in_production = models.BooleanField(default=True)
    abv = models.DecimalField(
        'Alcohol content (% by volume)',
        max_digits=4, decimal_places=2, blank=True, null=True,
    )
    ibu = models.PositiveSmallIntegerField(
        'Bitterness (International Bitterness Units)',
        blank=True, null=True,
    )
    color_srm = models.DecimalField(
        'Color (Standard Reference Method)',
        max_digits=4, decimal_places=1, blank=True, null=True,
    )
    untappd_url = models.URLField(blank=True, null=True, unique=True)
    beer_advocate_url = models.URLField(
        'BeerAdvocate URL (if known)', null=True, blank=True, unique=True,
    )
    rate_beer_url = models.URLField(blank=True, null=True, unique=True)
    logo_url = models.URLField(blank=True, null=True)
    color_html = models.CharField(
        'HTML Color (in hex)', max_length=9,  # #00112233 -> RGBA
        blank=True,
    )
    api_vendor_style = models.CharField(
        'API vendor-provided style (hidden from API)', max_length=100,
        blank=True,
    )
    manufacturer_url = models.URLField(blank=True, null=True, unique=True)
    automatic_updates_blocked = models.NullBooleanField(default=False)
    taphunter_url = models.URLField(blank=True, null=True, unique=True)
    stem_and_stein_pk = models.PositiveIntegerField(
        blank=True, null=True, unique=True,
    )
    taplist_io_pk = models.PositiveIntegerField(
        blank=True, null=True, unique=True,
    )
    time_first_seen = models.DateTimeField(blank=True, null=True, default=now)
    tweeted_about = models.BooleanField(default=False, db_index=True)
    beermenus_slug = models.CharField(
        max_length=250, blank=True, null=True, unique=True,
    )

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

    def __str__(self):
        return self.name

    def render_srm(self):
        if self.color_html:
            return self.color_html
        return render_srm(self.color_srm)

    def merge_from(self, other):
        LOG.info('merging %s into %s', other, self)
        with transaction.atomic():
            Tap.objects.filter(beer=other).update(beer=self)
            BeerAlternateName.objects.filter(beer=other).update(beer=self)
            try:
                with transaction.atomic():
                    BeerPrice.objects.filter(beer=other).update(beer=self)
            except IntegrityError:
                LOG.warning('Duplicate prices detected for %s', self)
                prices_updated = BeerPrice.objects.filter(beer=other).exclude(
                    venue__in=models.Subquery(
                        BeerPrice.objects.filter(beer=self).values('venue')
                    ),
                ).update(beer=self)
                prices_deleted = BeerPrice.objects.filter(beer=other).delete()
                LOG.info(
                    'Updated %s prices and deleted %s prices',
                    prices_updated,
                    prices_deleted,
                )
            excluded_fields = {
                'name' 'in_production', 'automatic_updates_blocked',
                'manufacturer', 'id', 'time_first_seen',
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
                BeerAlternateName.objects.update_or_create(
                    name=other.name,
                    beer=self,
                )
            if other.time_first_seen:
                if not self.time_first_seen or \
                        self.time_first_seen > other.time_first_seen:
                    self.time_first_seen = other.time_first_seen
            other.delete()
            self.save()

    class Meta:
        unique_together = [
            ('name', 'manufacturer'),
        ]


class BeerAlternateName(models.Model):
    beer = models.ForeignKey(Beer, models.CASCADE, related_name='alternate_names')
    name = CITextField()

    def __str__(self):
        return f'{self.name} for {self.beer_id}'


class ManufacturerAlternateName(models.Model):
    manufacturer = models.ForeignKey(
        Manufacturer, models.CASCADE, related_name='alternate_names')
    name = CITextField()

    def __str__(self):
        return f'{self.name} for {self.manufacturer_id}'


class ServingSize(models.Model):
    name = models.CharField(max_length=50, unique=True)
    # max 9999.9 oz
    volume_oz = models.DecimalField(
        unique=True, null=True, blank=True,
        max_digits=5, decimal_places=1,
    )

    def __str__(self):
        return self.name


class BeerPrice(models.Model):
    beer = models.ForeignKey(Beer, models.CASCADE, related_name='prices')
    venue = models.ForeignKey(
        'venues.Venue', models.CASCADE, related_name='beer_prices',
    )
    serving_size = models.ForeignKey(
        ServingSize, models.DO_NOTHING, related_name='beer_prices',
    )
    # max $999.99
    price = models.DecimalField(
        max_digits=5, decimal_places=2,
    )

    def __str__(self):
        return f'${self.price} for {self.beer_id} at {self.venue_id}'

    class Meta:
        unique_together = (
            ('beer', 'venue', 'serving_size'),
        )


class UntappdMetadata(models.Model):
    json_data = JSONField()
    timestamp = models.DateTimeField(auto_now=True)
    beer = models.OneToOneField(
        Beer, models.CASCADE, related_name='untappd_metadata',
    )
