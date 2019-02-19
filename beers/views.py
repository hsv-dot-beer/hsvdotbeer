from django.db.models import Prefetch
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404

from taps.models import Tap
from venues.serializers import VenueSerializer
from venues.models import Venue
from venues.filters import VenueFilterSet

from . import serializers
from . import models
from . import filters


class ModerationMixin():

    @action(detail=True, methods=['POST'])
    def mergefrom(self, request, pk):
        serializer = serializers.OtherPKSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = get_object_or_404(self.get_queryset(), id=pk)
        model = self.get_queryset().model
        try:
            other = self.get_queryset().get(id=serializer.validated_data['id'])
        except model.DoesNotExist:
            raise serializers.serializers.ValidationError({
                'id': [
                    f'A {model.__name__} with the given ID does not exist.',
                ],
            })
        instance.merge_from(other)
        instance.refresh_from_db()
        return Response(self.get_serializer(instance=instance).data)


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

    @action(detail=True, methods=['GET'])
    def beersontap(self, request, pk):
        """Get a list of beers on tap for this style"""
        queryset = BeerViewSet.queryset.filter(
            style__id=pk,
            taps__isnull=False,
        ).distinct()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BeerViewSet.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = BeerViewSet.serializer_class(queryset, many=True)
        return Response(serializer.data)


class ManufacturerViewSet(ModerationMixin, ModelViewSet):
    serializer_class = serializers.ManufacturerSerializer
    queryset = models.Manufacturer.objects.order_by('name')


class BeerViewSet(ModerationMixin, ModelViewSet):
    serializer_class = serializers.BeerSerializer
    queryset = models.Beer.objects.select_related(
        'manufacturer', 'style',
    ).prefetch_related(
        Prefetch(
            'taps',
            queryset=Tap.objects.select_related(
                'venue',
            ),
        ),
    ).order_by('manufacturer__name', 'name')
    filterset_class = filters.BeerFilterSet

    @action(detail=True, methods=['GET'])
    def placesavailable(self, request, pk):
        """Get all the venues at which the given beer is on tap"""
        queryset = Venue.objects.filter(taps__beer__id=pk).distinct().order_by(
            'name',
        )
        # let the user use all the venue filters just for kicks
        queryset = VenueFilterSet(request.query_params, queryset=queryset).qs

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = VenueSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = VenueSerializer(queryset, many=True)
        return Response(serializer.data)
