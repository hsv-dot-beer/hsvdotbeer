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

    def get_tap_list_provider_display(self, obj):
        # Give the user the fancy formatted version in read-only form
        return obj.get_tap_list_provider_display()

    class Meta:
        model = models.Venue
        fields = '__all__'


class VenueAPIConfigurationSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.VenueAPIConfiguration
        fields = '__all__'
