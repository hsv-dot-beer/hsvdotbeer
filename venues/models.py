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
        ('manual', 'Chalkboard/Whiteboard'),
        ('', 'Unknown'),
        ('test', 'TEST LOCAL PROVIDER'),
        ('stemandstein', 'The Stem & Stein\'s HTML'),
        ('taplist.io', 'taplist.io'),
        ('beermenus', 'BeerMenus'),
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
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=50, blank=True)
    logo_url = models.URLField(blank=True)
    slug = models.SlugField()
    on_downtown_craft_beer_trail = models.BooleanField(default=False)
    # -90 to +90
    latitude = models.DecimalField(
        max_digits=10, decimal_places=8, blank=True, null=True,
    )
    # -180 to 180
    longitude = models.DecimalField(
        max_digits=11, decimal_places=8, blank=True, null=True,
    )
    twitter_short_location_description = models.CharField(
        'Short location description for this specific location for use on '
        'Twitter', max_length=25, blank=True,
    )

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
    taphunter_excluded_lists = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        null=True,
    )
    taplist_io_display_id = models.CharField(max_length=50, blank=True)
    taplist_io_access_code = models.CharField(max_length=50, blank=True)
    beermenus_categories = ArrayField(
        models.TextField(),
        default=list,
        blank=True,
        null=True,
    )
    beermenus_slug = models.CharField(max_length=250, blank=True)
