"""Models for tap list provider support"""
from django.db import models

from venues.models import Venue


class APIRateLimitTimestamp(models.Model):
    api_type = models.CharField(
        max_length=50,
        unique=True,
        choices=Venue.TAP_LIST_PROVIDERS,
    )
    rate_limit_expires_at = models.DateTimeField()
