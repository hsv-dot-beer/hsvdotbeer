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
