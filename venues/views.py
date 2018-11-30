from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser

from . import serializers
from . import models


class VenueViewSet(ModelViewSet):
    serializer_class = serializers.VenueSerializer
    queryset = models.Venue.objects.order_by('name')


class VenueAPIConfigurationViewSet(ModelViewSet):
    serializer_class = serializers.VenueAPIConfigurationSerializer
    queryset = models.VenueAPIConfiguration.objects.all()
    permission_classes = (IsAdminUser, )


class RoomViewSet(ModelViewSet):
    serializer_class = serializers.RoomSerializer
    queryset = models.Room.objects.select_related('venue').order_by(
        'venue__name', 'name',
    )
