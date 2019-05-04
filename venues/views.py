from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response

from beers.views import CachedListMixin
from . import serializers
from . import models
from . import filters


class VenueViewSet(CachedListMixin, ModelViewSet):
    serializer_class = serializers.VenueSerializer
    queryset = models.Venue.objects.order_by('name')
    filterset_class = filters.VenueFilterSet

    @method_decorator(cache_page(60 * 5))
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


class VenueAPIConfigurationViewSet(CachedListMixin, ModelViewSet):
    serializer_class = serializers.VenueAPIConfigurationSerializer
    queryset = models.VenueAPIConfiguration.objects.all()
    permission_classes = (IsAdminUser, )
