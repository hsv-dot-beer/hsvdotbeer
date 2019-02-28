from django_filters.rest_framework import (
    FilterSet, OrderingFilter, CharFilter,
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
            'name', 'abv', 'ibu', 'style__name', 'style__category__name',
            'manufacturer__name',
        ],
    )

    search = CharFilter(method='filter_search')

    def filter_search(self, queryset, name, value):
        return self.queryset.filter(
            Q(name__icontains=value) | Q(alternate_names__name__icontains=value) | Q(
                manufacturer__name__icontains=value
            ) | Q(style__name__icontains=value) | Q(style__category__name__icontains=value),
        ).distinct()

    class Meta:
        fields = {
            'name': DEFAULT_STRING_FILTER_OPERATORS,
            'abv': DEFAULT_NUMERIC_FILTER_OPERATORS,
            'ibu': DEFAULT_NUMERIC_FILTER_OPERATORS,
            'manufacturer__name': DEFAULT_NUMERIC_FILTER_OPERATORS,
            'taps__venue__name': DEFAULT_STRING_FILTER_OPERATORS,
            'style__name': DEFAULT_STRING_FILTER_OPERATORS,
            'style__category__name': DEFAULT_STRING_FILTER_OPERATORS,
            'search': ['exact'],
        }
        model = models.Beer
