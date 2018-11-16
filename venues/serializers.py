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


class RoomSerializer(serializers.ModelSerializer):
    venue_id = serializers.PrimaryKeyRelatedField(
        write_only=True, allow_null=False, required=True,
        queryset=models.Venue.objects.all(),
    )
    venue = VenueSerializer(read_only=True)

    def validate(self, data):
        try:
            data['venue'] = data.pop('venue_id')
        except KeyError:
            # in a PATCH; don't care
            pass
        return data

    class Meta:
        model = models.Room
        fields = '__all__'
