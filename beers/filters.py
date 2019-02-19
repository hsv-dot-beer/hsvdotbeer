from django_filters.rest_framework import (
    FilterSet, OrderingFilter,
)

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

    class Meta:
        fields = {
            'name': DEFAULT_STRING_FILTER_OPERATORS,
            'abv': DEFAULT_NUMERIC_FILTER_OPERATORS,
            'ibu': DEFAULT_NUMERIC_FILTER_OPERATORS,
            'manufacturer__name': DEFAULT_NUMERIC_FILTER_OPERATORS,
            'taps__venue__name': DEFAULT_STRING_FILTER_OPERATORS,
            'style__name': DEFAULT_STRING_FILTER_OPERATORS,
            'style__category__name': DEFAULT_STRING_FILTER_OPERATORS,
        }
        model = models.Beer
