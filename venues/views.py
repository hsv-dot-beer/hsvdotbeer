from rest_framework.viewsets import ModelViewSet

from . import serializers
from . import models


class VenueViewSet(ModelViewSet):
    serializer_class = serializers.VenueSerializer
    queryset = models.Venue.objects.order_by('name')
