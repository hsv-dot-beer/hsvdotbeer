from django.db import models

class BeerStyle(models.Model):
    CLASS_CHOICES = (
        ('beer', 'Beer'),
        ('cider', 'Cider'),
        ('mead', 'Mead'),
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100)
    revision = models.CharField(max_length=10)

    bjcp_class = models.CharField(max_length=10, choices=CLASS_CHOICES)

    category = models.CharField(max_length=2)
    subcategory = models.CharField(max_length=2)

    category_name = models.CharField(max_length=255)
    category_notes = models.CharField(max_length=255)

    ibu_low = models.FloatField(null=True)
    ibu_high = models.FloatField(null=True)
    og_low = models.FloatField(null=True)
    og_high = models.FloatField(null=True)
    fg_low = models.FloatField(null=True)
    fg_high = models.FloatField(null=True)
    srm_low = models.FloatField(null=True)
    srm_high = models.FloatField(null=True)
    abv_low = models.FloatField(null=True)
    abv_high = models.FloatField(null=True)

    aroma = models.CharField(max_length=255, blank=True, null=True)
    appearance = models.CharField(max_length=255, blank=True, null=True)
    flavor = models.CharField(max_length=255, blank=True, null=True)
    mouthfeel = models.CharField(max_length=255, blank=True, null=True)
    impression = models.CharField(max_length=255, blank=True, null=True)
    comments = models.CharField(max_length=255, blank=True, null=True)
    history = models.CharField(max_length=255, blank=True, null=True)
    ingredients = models.CharField(max_length=255, blank=True, null=True)
    comparison = models.CharField(max_length=255, blank=True, null=True)
    examples = models.CharField(max_length=255, blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, null=True)
