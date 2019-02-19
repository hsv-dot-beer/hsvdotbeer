from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser

from . import serializers
from . import models
from . import filters


class VenueViewSet(ModelViewSet):
    serializer_class = serializers.VenueSerializer
    queryset = models.Venue.objects.order_by('name')
    filterset_class = filters.VenueFilterSet


class VenueAPIConfigurationViewSet(ModelViewSet):
    serializer_class = serializers.VenueAPIConfigurationSerializer
    queryset = models.VenueAPIConfiguration.objects.all()
    permission_classes = (IsAdminUser, )
