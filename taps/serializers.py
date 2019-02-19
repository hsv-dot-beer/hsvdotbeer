from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from django.utils import timezone

from venues.models import Venue
from venues.serializers import VenueSerializer

from . import models


class TapSerializer(serializers.ModelSerializer):
    venue_id = serializers.PrimaryKeyRelatedField(
        write_only=True, allow_null=False, required=True,
        queryset=Venue.objects.all(),
    )
    estimated_percent_remaining = serializers.FloatField(
        min_value=0, max_value=100, allow_null=True, required=False,
    )
    venue = VenueSerializer(read_only=True)
    time_added = serializers.DateTimeField(read_only=True)
    time_updated = serializers.DateTimeField(read_only=True)

    def update(self, instance, validated_data):
        instance.time_updated = timezone.now()
        return super().update(instance, validated_data)

    def validate(self, data):
        try:
            data['venue'] = data.pop('venue_id')
        except KeyError:
            pass
        return data

    class Meta:
        fields = '__all__'
        model = models.Tap
        validators = [
            UniqueTogetherValidator(
                queryset=models.Tap.objects.all(),
                fields=('tap_number', 'venue_id'),
            ),
        ]
