from django.db import models


class Event(models.Model):
    venue = models.ForeignKey(
        'venues.Venue', models.CASCADE, related_name='events',
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    title = models.CharField(max_length=50, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['venue', 'start_time']),
            models.Index(fields=['venue', 'end_time']),
        ]
