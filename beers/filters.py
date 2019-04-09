from django_filters.rest_framework import (
    FilterSet, OrderingFilter, CharFilter, BooleanFilter,
)
from django.db.models import Q

from . import models

DEFAULT_NUMERIC_FILTER_OPERATORS = [
    'exact', 'lte', 'gte', 'lt', 'gt', 'isnull', 'in',
]

DEFAULT_STRING_FILTER_OPERATORS = [
    'iexact', 'icontains', 'istartswith', 'iendswith', 'startswith',
    'endswith', 'contains', 'exact', 'regex', 'iregex', 'isnull', 'in',
]


class BeerFilterSet(FilterSet):

    o = OrderingFilter(
        fields=[
            'name', 'abv', 'ibu', 'style__name',
            'style__alternate_names__name', 'manufacturer__name',
        ],
    )

    search = CharFilter(method='filter_search')
    on_tap = BooleanFilter(method='filter_on_tap')

    def filter_search(self, queryset, name, value):
        return self.queryset.filter(
            Q(
                name__icontains=value,
            ) | Q(
                alternate_names__name__icontains=value,
            ) | Q(
                manufacturer__name__icontains=value,
            ) | Q(
                # the field is case-insensitive, so no need for icontains
                style__name=value,
            ) | Q(
                # the field is case-insensitive, so no need for icontains
                style__alternate_names__name=value,
            ) | Q(
                manufacturer__alternate_names__name__icontains=value,
            ),
        ).distinct()

    def filter_on_tap(self, queryset, name, value):
        return queryset.filter(taps__isnull=not value)

    class Meta:
        fields = {
            'name': DEFAULT_STRING_FILTER_OPERATORS,
            'abv': DEFAULT_NUMERIC_FILTER_OPERATORS,
            'ibu': DEFAULT_NUMERIC_FILTER_OPERATORS,
            'manufacturer__name': DEFAULT_NUMERIC_FILTER_OPERATORS,
            'taps__venue__name': DEFAULT_STRING_FILTER_OPERATORS,
            'style__name': DEFAULT_STRING_FILTER_OPERATORS,
            'style__alternate_names__name': DEFAULT_STRING_FILTER_OPERATORS,
            'search': ['exact'],
            'on_tap': ['exact'],
        }
        model = models.Beer
