import string

from django.db import models


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

    category = models.ForeignKey(BeerStyleCategory, on_delete='CASCADE')
    tags = models.ManyToManyField(BeerStyleTag, blank=True)

    ibu_low = models.PositiveSmallIntegerField(default=0)
    ibu_high = models.PositiveSmallIntegerField(default=0)
    srm_low = models.PositiveSmallIntegerField(default=0)
    srm_high = models.PositiveSmallIntegerField(default=0)

    og_low = models.DecimalField(max_digits=4, decimal_places=3, default=0)
    og_high = models.DecimalField(max_digits=4, decimal_places=3, default=0)
    fg_low = models.DecimalField(max_digits=4, decimal_places=3, default=0)
    fg_high = models.DecimalField(max_digits=4, decimal_places=3, default=0)

    abv_low = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    abv_high = models.DecimalField(max_digits=3, decimal_places=1, default=0)

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

    def __str__(self):
        return self.name


class Beer(models.Model):
    name = models.CharField(max_length=25, db_index=True)
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
    untappd_id = models.CharField(
        'Untappd ID (if known)', max_length=50, null=True, blank=True,
        unique=True,
    )
    beer_advocate_id = models.CharField(
        'BeerAdvocate ID (if known)', max_length=50, null=True, blank=True,
        unique=True,
    )
    rate_beer_url = models.URLField(blank=True, null=True, unique=True)

    def save(self, *args, **kwargs):
        # force empty IDs to null to avoid running afoul of unique constraints
        if not self.untappd_id:
            self.untappd_id = None
        if not self.beer_advocate_id:
            self.beer_advocate_id = None
        if not self.rate_beer_url:
            self.rate_beer_url = None
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def render_srm(self):
        """Convert the SRM to a valid HTML string (if known)"""
        if not self.color_srm:
            return '#ffffff'
        # round the color to an int and put it in the inclusive range [1, 30]
        int_color = min([int(self.color_srm), 30])
        if int_color < 1:
            int_color = 1
        # source:
        # https://www.homebrewtalk.com/forum/threads/ebc-or-srm-to-color-rgb.78018/#post-820969
        color_map = {
            1: '#F3F993',
            2: '#F5F75C',
            3: '#F6F513',
            4: '#EAE615',
            5: '#E0D01B',
            6: '#D5BC26',
            7: '#CDAA37',
            8: '#C1963C',
            9: '#BE8C3A',
            10: '#BE823A',
            11: '#C17A37',
            12: '#BF7138',
            13: '#BC6733',
            14: '#B26033',
            15: '#A85839',
            16: '#985336',
            17: '#8D4C32',
            18: '#7C452D',
            19: '#6B3A1E',
            20: '#5D341A',
            21: '#4E2A0C',
            22: '#4A2727',
            23: '#361F1B',
            24: '#261716',
            25: '#231716',
            26: '#19100F',
            27: '#16100F',
            28: '#120D0C',
            29: '#100B0A',
            30: '#050B0A',
        }
        return color_map[int_color]

    class Meta:
        unique_together = [
            ('name', 'manufacturer'),
        ]
