from django.db.models import Prefetch
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response

from beers.serializers import BeerStyleWithBeersSerializer, \
    BeerStyleCategoryWithBeersSerializer

from . import serializers
from . import models
from . import filters


class VenueViewSet(ModelViewSet):
    serializer_class = serializers.VenueSerializer
    queryset = models.Venue.objects.order_by('name')
    filterset_class = filters.VenueFilterSet

    @action(detail=True, methods=['GET'])
    def beers(self, request, pk):
        from beers.views import BeerViewSet
        from beers.filters import BeerFilterSet

        queryset = BeerViewSet.queryset.filter(
            taps__venue__id=pk,
        ).distinct()

        # let the user use all the beer filters just for kicks
        queryset = BeerFilterSet(request.query_params, queryset=queryset).qs

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BeerViewSet.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = BeerViewSet.serializer_class(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def styles(self, request, pk):
        from beers.views import BeerStyleViewSet, BeerViewSet
        queryset = BeerStyleViewSet.queryset.filter(
            beers__taps__venue__id=pk,
        ).prefetch_related(
            Prefetch(
                'beers',
                queryset=BeerViewSet.queryset.filter(
                    taps__isnull=False,
                ).distinct(),
            ),
        ).distinct()

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BeerStyleWithBeersSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = BeerStyleWithBeersSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def stylecategories(self, request, pk):
        from beers.views import BeerStyleCategoryViewSet, BeerViewSet
        queryset = BeerStyleCategoryViewSet.queryset.filter(
            styles__beers__taps__venue__id=pk,
        ).prefetch_related(
            Prefetch(
                'styles__beers',
                queryset=BeerViewSet.queryset.filter(
                    taps__isnull=False,
                ).distinct(),
            ),
        ).distinct()

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = BeerStyleCategoryWithBeersSerializer(
                page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = BeerStyleCategoryWithBeersSerializer(
            queryset, many=True)
        return Response(serializer.data)


class VenueAPIConfigurationViewSet(ModelViewSet):
    serializer_class = serializers.VenueAPIConfigurationSerializer
    queryset = models.VenueAPIConfiguration.objects.all()
    permission_classes = (IsAdminUser, )
