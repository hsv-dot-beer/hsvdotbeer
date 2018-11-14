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
    notes = models.TextField(default='')
    category_id = models.CharField(max_length=2, unique=True)
    revision = models.CharField(max_length=10, default='2015')

    def __str__(self):
        return self.name


class BeerStyleTag(models.Model):
    tag = models.CharField(max_length=50, unique=True, db_index=True)

    def __str__(self):
        return self.tag


class BeerStyle(models.Model):
    name = models.CharField(max_length=255)
    subcategory = models.CharField(max_length=1, choices=zip(string.ascii_uppercase, string.ascii_uppercase))

    category = models.ForeignKey(BeerStyleCategory, on_delete='CASCADE')
    tags = models.ManyToManyField(BeerStyleTag)

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

    aroma = models.TextField(default='')
    appearance = models.TextField(default='')
    flavor = models.TextField(default='')
    mouthfeel = models.TextField(default='')
    impression = models.TextField(default='')
    comments = models.TextField(default='')
    history = models.TextField(default='')
    ingredients = models.TextField(default='')
    comparison = models.TextField(default='')
    examples = models.TextField(default='')

    def __str__(self):
        return self.name

