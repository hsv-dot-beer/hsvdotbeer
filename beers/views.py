from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from django.db.models import Prefetch

from taps.models import Tap

from . import serializers
from . import models
from . import filters


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


class BeerViewSet(ModelViewSet):
    serializer_class = serializers.BeerSerializer
    queryset = models.Beer.objects.select_related(
        'manufacturer', 'style',
    ).order_by('manufacturer__name', 'name')
    filterset_class = filters.BeerFilterSet

    @action(detail=False, methods=['GET'])
    def places_available(self, request):
        queryset = models.Beer.objects.select_related('manufacturer').prefetch_related(Prefetch('taps', queryset=Tap.objects.select_related('room__venue')))
        serializer = serializers.BeerVenueSerializer(queryset, many=True)

        return Response(serializer.data)





