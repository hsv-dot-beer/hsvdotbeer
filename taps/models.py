from django.db import models
from django.utils import timezone


class Tap(models.Model):

    GAS_CHOICES = [
        ('co2', 'CO₂'),
        ('nitro', 'Nitro'),
        ('', 'Unknown'),
    ]
    venue = models.ForeignKey(
        'venues.Venue',
        models.CASCADE,
        related_name='taps',
        blank=True, null=True,
    )
    # going out on a limb and assuming a single venue won't have more than
    # 32,767 taps...
    tap_number = models.PositiveSmallIntegerField()
    beer = models.ForeignKey(
        'beers.Beer', models.DO_NOTHING, blank=True, null=True,
        related_name='taps',
    )
    gas_type = models.CharField(max_length=5, choices=GAS_CHOICES, blank=True)
    estimated_percent_remaining = models.FloatField(blank=True, null=True)
    time_added = models.DateTimeField(default=timezone.now)
    time_updated = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = (
            ('venue', 'tap_number'),
        )
