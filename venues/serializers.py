"""Serializers for venues"""


from rest_framework import serializers
from django_countries.serializers import CountryFieldMixin

from .fields import TimeZoneField
from . import models


class VenueSerializer(CountryFieldMixin, serializers.ModelSerializer):

    time_zone = TimeZoneField(
        required=False, allow_blank=False, allow_null=False,
    )
    tap_list_provider_display = serializers.SerializerMethodField()
    latitude = serializers.DecimalField(
        max_digits=10, decimal_places=8, min_value=-90, max_value=90,
        required=False, allow_null=True,
    )
    longitude = serializers.DecimalField(
        max_digits=11, decimal_places=8, min_value=-180, max_value=180,
        required=False, allow_null=True,
    )

    def get_tap_list_provider_display(self, obj):
        # Give the user the fancy formatted version in read-only form
        return obj.get_tap_list_provider_display()

    class Meta:
        model = models.Venue
        fields = '__all__'
        # something is not interacting well between nullable urls and DRF's
        # validation. Marking this read-only for now.

        # also marking the on_downtown_craft_beer_trail field as read-only
        # to protect us from ourselves
        read_only_fields = ['untappd_url', 'on_downtown_craft_beer_trail']


class VenueBySlugSerializer(VenueSerializer):
    class Meta(VenueSerializer.Meta):
        lookup_field = 'slug'


class VenueAPIConfigurationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.VenueAPIConfiguration
        fields = '__all__'
