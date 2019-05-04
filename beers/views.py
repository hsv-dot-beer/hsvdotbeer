
from django.db.utils import IntegrityError
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page
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


class CachedListMixin():
    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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


class ManufacturerViewSet(CachedListMixin, ModerationMixin, ModelViewSet):
    serializer_class = serializers.ManufacturerSerializer
    queryset = models.Manufacturer.objects.order_by('name')


class BeerViewSet(CachedListMixin, ModerationMixin, ModelViewSet):
    serializer_class = serializers.BeerSerializer
    queryset = models.Beer.objects.select_related(
        'manufacturer', 'style', 'untappd_metadata', 'style',
    ).prefetch_related(
        'style__alternate_names',
        Prefetch(
            'taps',
            queryset=Tap.objects.select_related(
                'venue',
            ),
        ),
        Prefetch(
            'prices',
            queryset=models.BeerPrice.objects.select_related(
                'venue', 'serving_size',
            )
        ),
    ).order_by('manufacturer__name', 'name')
    filterset_class = filters.BeerFilterSet

    @method_decorator(cache_page(60 * 5))
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


class StyleMergeView(TemplateView):

    def get(self, request):
        user = request.user
        if not user.is_staff:
            return redirect(f'/{reverse("admin:login")}/?next={request.path}')
        if 'ids' not in request.GET:
            return HttpResponse('you must specify IDs', status=400)
        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['styles'] = models.Style.objects.filter(
            id__in=context['view'].request.GET['ids'].split(','),
        ).prefetch_related('alternate_names')
        context['back_link'] = reverse('admin:beers_style_changelist')

        return context

    def post(self, request):
        try:
            all_pks = [int(i) for i in request.POST['all-styles'].split(',')]
            kept_pk = int(request.POST['styles'])
        except (KeyError, ValueError) as exc:
            print(exc, request.POST)
            return HttpResponse('Invalid data received!', status=400)
        styles = models.Style.objects.filter(id__in=all_pks).prefetch_related(
            'alternate_names', 'beers',
        )
        try:
            desired_style = [i for i in styles if i.id == kept_pk][0]
        except IndexError:
            return HttpResponse(
                'Chosen style was not part of the list!', status=400,
            )
        try:
            desired_style.merge_from(styles)
        except IntegrityError:
            return HttpResponse(
                'At least one of the beers has an alternate name that '
                'conflicts', status=400,
            )
        except ValueError as exc:
            return HttpResponse(str(exc), status=400)
        return redirect(reverse('admin:beers_style_changelist'))

    template_name = 'beers/merge_styles.html'
