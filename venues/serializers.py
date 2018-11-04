"""Serializers for venues"""


from rest_framework import serializers
from django_countries.serializers import CountryFieldMixin

from .fields import TimeZoneField
from . import models


class VenueSerializer(CountryFieldMixin, serializers.ModelSerializer):

    time_zone = TimeZoneField(
        required=False, allow_blank=False, allow_null=False,
    )

    class Meta:
        model = models.Venue
        fields = '__all__'
        read_only_fields = ['id', ]
