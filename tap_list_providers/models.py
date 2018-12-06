"""Models for tap list provider support"""

from django.db import models


from venues.models import Venue


class TapListProviderStyleMapping(models.Model):
    provider = models.CharField(
        max_length=20, choices=Venue.TAP_LIST_PROVIDERS,
    )
    provider_style_name = models.CharField(max_length=50)
    style = models.ForeignKey(
        'beers.BeerStyle', models.CASCADE,
        related_name='tap_list_provider_mappings',
    )

    class Meta:
        unique_together = (
            ('provider', 'provider_style_name'),
        )
