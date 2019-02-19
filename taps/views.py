from rest_framework.viewsets import ModelViewSet

from . import serializers
from . import models


class TapViewSet(ModelViewSet):
    serializer_class = serializers.TapSerializer
    queryset = models.Tap.objects.select_related('venue').order_by('id')
