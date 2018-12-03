from django.db import models


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
    # TODO add beer FK (optional)
    gas_type = models.CharField(max_length=5, choices=GAS_CHOICES, blank=True)
    estimated_percent_remaining = models.FloatField(blank=True, null=True)

    class Meta:
        unique_together = (
            ('room', 'tap_number'),
        )
