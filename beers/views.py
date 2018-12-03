from rest_framework.viewsets import ModelViewSet

from . import serializers
from . import models


class BeerStyleCategoryViewSet(ModelViewSet):
    serializer_class = serializers.BeerStyleCategorySerializer
    queryset = models.BeerStyleCategory.objects.order_by('id')


class BeerStyleTagViewSet(ModelViewSet):
    serializer_class = serializers.BeerStyleTagSerializer
    queryset = models.BeerStyleTag.objects.order_by('tag')


class BeerStyleViewSet(ModelViewSet):
    serializer_class = serializers.BeerStyleSerializer
    queryset = models.BeerStyle.objects.select_related(
        'category',
    ).prefetch_related('tags').order_by('id')


class ManufacturerViewSet(ModelViewSet):
    serializer_class = serializers.ManufacturerSerializer
    queryset = models.Manufacturer.objects.order_by('name')
