from django_filters.rest_framework import (
    FilterSet, OrderingFilter, CharFilter, BooleanFilter,
)
from django.db.models import Q, F

from . import models

DEFAULT_NUMERIC_FILTER_OPERATORS = [
    'exact', 'lte', 'gte', 'lt', 'gt', 'isnull', 'in',
]

DEFAULT_STRING_FILTER_OPERATORS = [
    'iexact', 'icontains', 'istartswith', 'iendswith', 'startswith',
    'endswith', 'contains', 'exact', 'regex', 'iregex', 'isnull', 'in',
]


class BeerOrderingFilter(OrderingFilter):
    """Custom version of OrderingFilter that treats null ABVs as zero"""

    def get_ordering_value(self, param):
        value = super().get_ordering_value(param)
        if param.endswith('abv'):
            if param.startswith('-'):
                # if we're going high-to-low, put nulls at the end
                return F(value[1:]).desc(nulls_last=True)
            return F(value).asc(nulls_first=True)
        return value


class BeerFilterSet(FilterSet):

    o = BeerOrderingFilter(
        fields=[
            'name', 'abv', 'ibu', 'style__name',
            'style__alternate_names__name', 'manufacturer__name',
            'most_recently_added',
        ],
    )

    search = CharFilter(method='filter_search')
    on_tap = BooleanFilter(method='filter_on_tap')

    def filter_search(self, queryset, name, value):
        base_cond = Q()
        # what I want to search for:
        # each word (split by whitespace) is included in at least
        # one of the below six fields,
        # so you can search for "straight monkey" to get monkeynaut
        # or "belgi ipa ommeg" to get all Ommegang Belgian IPAs
        for word in value.split():
            base_cond &= Q(
                name__icontains=word,
            ) | Q(
                alternate_names__name__icontains=word,
            ) | Q(
                manufacturer__name__icontains=word,
            ) | Q(
                # the field is case-insensitive, so no need for icontains
                style__name=word,
            ) | Q(
                # the field is case-insensitive, so no need for icontains
                style__alternate_names__name=word,
            ) | Q(
                manufacturer__alternate_names__name__icontains=word,
            )
        queryset = queryset.filter(base_cond).distinct()
        return queryset

    def filter_on_tap(self, queryset, name, value):
        return queryset.filter(taps__isnull=not value).distinct()

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
            'taps__venue__slug': DEFAULT_STRING_FILTER_OPERATORS,
        }
        model = models.Beer
