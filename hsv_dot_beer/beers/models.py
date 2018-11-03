from django.db import models

class BeerStyle(models.Model):
    CLASS_CHOICES = (
        ('beer', 'Beer'),
        ('cider', 'Cider'),
        ('mead', 'Mead'),
    )

    bjcp_class = models.CharField(max_length=10, choices=CLASS_CHOICES)

    category_id = models.CharField(max_length=2)
    subcategory_id = models.CharField(max_length=1)

    category_name = models.CharField(max_length=100)
    category_notes = models.CharField(max_length=100)

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

    ibu_min = models.FloatField()
    ibu_max = models.FloatField()
    og_min = models.FloatField()
    og_max = models.FloatField()
    fg_min = models.FloatField()
    fg_max = models.FloatField()
    srm_min = models.FloatField()
    srm_max = models.FloatField()
    abv_min = models.FloatField()
    abv_max = models.FloatField()

    aroma = models.CharField(blank=True, null=True)
    appearance = models.CharField(blank=True, null=True)
    flavor = models.CharField(blank=True, null=True)
    mouthfeel = models.CharField(blank=True, null=True)
    impression = models.CharField(blank=True, null=True)
    comments = models.CharField(blank=True, null=True)
    history = models.CharField(blank=True, null=True)
    ingredients = models.CharField(blank=True, null=True)
    comparison = models.CharField(blank=True, null=True)
    examples = models.CharField(blank=True, null=True)
    tags = models.CharField(blank=True, null=True)
