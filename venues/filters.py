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


class VenueFilterSet(FilterSet):

    o = OrderingFilter(
        fields=[
            'name', 'rooms__taps__beer__name'
            'rooms__taps__beer__style__name',
            'rooms__taps__beer__style__category__name',
        ],
    )

    class Meta:
        fields = {
            'name': DEFAULT_STRING_FILTER_OPERATORS,
            'rooms__taps__beer__name': DEFAULT_STRING_FILTER_OPERATORS,
            'rooms__taps__beer__style__name': DEFAULT_STRING_FILTER_OPERATORS,
            'rooms__taps__beer__style__category__name': DEFAULT_STRING_FILTER_OPERATORS,
        }
        model = models.Venue
