import string

from django.db import models

class BeerStyle(models.Model):
    CLASS_CHOICES = (
        ('beer', 'Beer'),
        ('cider', 'Cider'),
        ('mead', 'Mead'),
    )

    name = models.CharField(max_length=255)
    revision = models.CharField(max_length=10)

    bjcp_class = models.CharField(max_length=10, choices=CLASS_CHOICES)

    category = models.CharField(max_length=2)
    subcategory = models.CharField(max_length=1, choices=zip(string.ascii_uppercase, string.ascii_uppercase))

    category_name = models.CharField(max_length=255)
    category_notes = models.CharField(max_length=255)

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

    aroma = models.CharField(max_length=255, blank=True, default='')
    appearance = models.CharField(max_length=255, blank=True, default='')
    flavor = models.CharField(max_length=255, blank=True, default='')
    mouthfeel = models.CharField(max_length=255, blank=True, default='')
    impression = models.CharField(max_length=255, blank=True, default='')
    comments = models.CharField(max_length=255, blank=True, default='')
    history = models.CharField(max_length=255, blank=True, default='')
    ingredients = models.CharField(max_length=255, blank=True, default='')
    comparison = models.CharField(max_length=255, blank=True, default='')
    examples = models.CharField(max_length=255, blank=True, default='')
    tags = models.CharField(max_length=255, blank=True, default='')
