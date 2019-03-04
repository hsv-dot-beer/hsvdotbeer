"""Models related to Venues"""

from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from timezone_field.fields import TimeZoneField
from django_countries.fields import CountryField


class Venue(models.Model):
    """A location that serves alcohol"""

    TAP_LIST_PROVIDERS = (
        ('untappd', 'Untappd'),
        ('digitalpour', 'DigitalPour'),
        ('taphunter', 'TapHunter'),
        ('nook_html', 'The Nook\'s static HTML'),
        ('manual', 'Chalkboard/Whiteboard'),
        ('', 'Unknown'),
        ('test', 'TEST LOCAL PROVIDER'),
        ('stemandstein', 'The Stem & Stein\'s HTML'),
    )

    # NOTE if this ever grows beyond HSV, we'll have to revisit uniqueness
    name = models.CharField(max_length=50, unique=True)
    address = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=25, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    country = CountryField(blank=True)
    time_zone = TimeZoneField(default=settings.DEFAULT_VENUE_TIME_ZONE)
    website = models.URLField(blank=True)
    facebook_page = models.URLField(blank=True)
    twitter_handle = models.CharField(blank=True, max_length=25)
    instagram_handle = models.CharField(blank=True, max_length=25)
    tap_list_provider = models.CharField(
        'What service the venue uses for digital tap lists',
        blank=True, max_length=30, choices=TAP_LIST_PROVIDERS,
    )
    untappd_url = models.URLField(blank=True, null=True, unique=True)

    def __str__(self):
        return self.name


class VenueAPIConfiguration(models.Model):
    venue = models.OneToOneField(
        Venue, models.CASCADE, related_name='api_configuration',
    )
    url = models.URLField(blank=True, null=True)
    api_key = models.CharField(max_length=100, blank=True)
    digital_pour_venue_id = models.CharField(max_length=50, blank=True)
    digital_pour_location_number = models.PositiveSmallIntegerField(
        blank=True, null=True,
    )
    untappd_location = models.PositiveIntegerField(blank=True, null=True)
    untappd_theme = models.PositiveIntegerField(blank=True, null=True)
    untappd_categories = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        null=True,
    )
    taphunter_location = models.CharField(max_length=50, blank=True)
