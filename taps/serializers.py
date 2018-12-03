from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from venues.models import Room
from venues.serializers import RoomSerializer

from . import models


class TapSerializer(serializers.ModelSerializer):
    room_id = serializers.PrimaryKeyRelatedField(
        write_only=True, allow_null=False, required=True,
        queryset=Room.objects.all(),
    )
    estimated_percent_remaining = serializers.FloatField(
        min_value=0, max_value=100, allow_null=True, required=False,
    )
    room = RoomSerializer(read_only=True)

    def validate(self, data):
        try:
            data['room'] = data.pop('room_id')
        except KeyError:
            pass
        return data

    class Meta:
        fields = '__all__'
        model = models.Tap
        validators = [
            UniqueTogetherValidator(
                queryset=models.Tap.objects.all(),
                fields=('tap_number', 'room_id'),
            ),
        ]
