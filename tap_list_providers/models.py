"""Models for tap list provider support"""

from django.db import models


class TapListProviderStyleMapping(models.Model):
    provider_style_name = models.CharField(max_length=50, unique=True)
    style = models.ForeignKey(
        'beers.BeerStyle', models.CASCADE,
        related_name='tap_list_provider_mappings',
    )
