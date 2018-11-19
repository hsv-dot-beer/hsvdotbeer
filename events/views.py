from rest_framework.viewsets import ModelViewSet

from . import models
from . import serializers


class EventViewSet(ModelViewSet):

    serializer_class = serializers.EventSerializer
    queryset = models.Event.objects.select_related('venue').order_by(
        'start_time', 'venue__name',
    )
