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
            'name', 'taps__beer__name'
            'taps__beer__style__name',
            'taps__beer__style__alternate_names__name',
            'on_downtown_craft_beer_trail',
        ],
    )

    class Meta:
        fields = {
            'name': DEFAULT_STRING_FILTER_OPERATORS,
            'taps__beer__name': DEFAULT_STRING_FILTER_OPERATORS,
            'taps__beer__style__name': DEFAULT_STRING_FILTER_OPERATORS,
            'taps__beer__style__alternate_names__name': DEFAULT_STRING_FILTER_OPERATORS,
            'on_downtown_craft_beer_trail': ['exact'],
        }
        model = models.Venue
