import logging
import string

from django.db import models, transaction

from .utils import render_srm

LOG = logging.getLogger(__name__)


class BeerStyleCategory(models.Model):
    CLASS_CHOICES = (
        ('beer', 'Beer'),
        ('cider', 'Cider'),
        ('mead', 'Mead'),
    )

    name = models.CharField(max_length=100, unique=True, db_index=True)
    bjcp_class = models.CharField(max_length=10, choices=CLASS_CHOICES, default='beer')
    notes = models.TextField(blank=True)
    category_id = models.PositiveSmallIntegerField()
    revision = models.CharField(max_length=10, default='2015')

    class Meta:
        unique_together = (('category_id', 'revision', 'bjcp_class'),)

    def __str__(self):
        return self.name


class BeerStyleTag(models.Model):
    tag = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.tag


class BeerStyle(models.Model):
    name = models.CharField(max_length=255)
    subcategory = models.CharField(max_length=1,
                                   choices=zip(string.ascii_uppercase, string.ascii_uppercase))

    category = models.ForeignKey(
        BeerStyleCategory, on_delete='CASCADE', related_name='styles',
    )
    tags = models.ManyToManyField(BeerStyleTag, blank=True)

    ibu_low = models.PositiveSmallIntegerField(
        'Minimum bitterness (International Bitterness Units)', default=0,
    )
    ibu_high = models.PositiveSmallIntegerField(
        'Maximum bitterness (International Bitterness Units)', default=0,
    )
    srm_low = models.PositiveSmallIntegerField(
        'Minimum color (Standard Reference Method)',
        default=0,
    )
    srm_high = models.PositiveSmallIntegerField(
        'Maximum color (Standard Reference Method)', default=0,
    )

    og_low = models.DecimalField(
        'Minimum original specific gravity',
        max_digits=4, decimal_places=3, default=0,
    )
    og_high = models.DecimalField(
        'Maximum original specific gravity',
        max_digits=4, decimal_places=3, default=0,
    )
    fg_low = models.DecimalField(
        'Minimum final specific gravity',
        max_digits=4, decimal_places=3, default=0,
    )
    fg_high = models.DecimalField(
        'Maximum final specific gravity',
        max_digits=4, decimal_places=3, default=0,
    )

    abv_low = models.DecimalField(
        'Maximum alcohol content (% by volume)',
        max_digits=3, decimal_places=1, default=0,
    )
    abv_high = models.DecimalField(
        'Minimum alcohol content (% by volume)',
        max_digits=3, decimal_places=1, default=0,
    )

    aroma = models.TextField(blank=True)
    appearance = models.TextField(blank=True)
    flavor = models.TextField(blank=True)
    mouthfeel = models.TextField(blank=True)
    impression = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    history = models.TextField(blank=True)
    ingredients = models.TextField(blank=True)
    comparison = models.TextField(blank=True)
    examples = models.TextField(blank=True)

    def render_srm_low(self):
        return render_srm(self.srm_low)

    def render_srm_high(self):
        return render_srm(self.srm_high)

    class Meta:
        unique_together = (('category', 'subcategory'),)

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    name = models.CharField(unique=True, max_length=100)
    url = models.URLField(blank=True)
    location = models.CharField(blank=True, max_length=50)
    logo_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    instagram_handle = models.CharField(max_length=50, blank=True)
    untappd_url = models.URLField(blank=True, unique=True, null=True)
    automatic_updates_blocked = models.NullBooleanField(default=False)
    taphunter_url = models.URLField(blank=True, null=True, unique=True)

    def merge_from(self, other):
        LOG.info('merging %s into %s', other, self)
        with transaction.atomic():
            other_beers = list(other.beers.all())
            my_beers = {i.name: i for i in self.beers.all()}
            for beer in other_beers:
                beer.manufacturer = self
                if beer.name in my_beers:
                    # we have a duplicate beer. Merge those two first.
                    # merge_from takes care of saving my_beer and deleting
                    # beer
                    # keep the one that was already present
                    my_beer = my_beers[beer.name]
                    my_beer.merge_from(beer)
                else:
                    # good
                    beer.save()

            for alternate_name in other.alternate_names.all():
                alternate_name.beer = self
                alternate_name.save()
            excluded_fields = {
                'name', 'automatic_updates_blocked', 'id',
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
            self.save()

    def __str__(self):
        return self.name


class Beer(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    style = models.ForeignKey(
        BeerStyle, models.DO_NOTHING, related_name='beers',
        # TODO: prevent this being null?
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
            for tap in other.taps.all():
                tap.beer = self
                tap.save()
            for alternate_name in other.alternate_names.all():
                alternate_name.beer = self
                alternate_name.save()
            excluded_fields = {
                'name' 'in_production', 'automatic_updates_blocked',
                'manufacturer', 'id',
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
            self.save()

    class Meta:
        unique_together = [
            ('name', 'manufacturer'),
        ]


class BeerAlternateName(models.Model):
    beer = models.ForeignKey(Beer, models.CASCADE, related_name='alternate_names')
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f'{self.name} for {self.beer_id}'


class ManufacturerAlternateName(models.Model):
    manufacturer = models.ForeignKey(
        Manufacturer, models.CASCADE, related_name='alternate_names')
    name = models.CharField(max_length=100, unique=True)

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
        'venues.Venue', models.DO_NOTHING, related_name='beer_prices',
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
