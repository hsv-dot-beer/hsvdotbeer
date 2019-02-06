from django.db import models
from django.utils import timezone


class Tap(models.Model):

    GAS_CHOICES = [
        ('co2', 'CO₂'),
        ('nitro', 'Nitro'),
        ('', 'Unknown'),
    ]
    room = models.ForeignKey(
        'venues.Room',
        models.CASCADE,
        related_name='taps',
    )
    # going out on a limb and assuming a single room won't have more than
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
            ('room', 'tap_number'),
        )
