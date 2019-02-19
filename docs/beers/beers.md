# Beers

## Filtering

You can look up beers by the following fields:

- `name` (Beer name)
- `abv` (Alcohol by volume)
- `__ibu` (International Bitterness Units)
- `manufacturer__name` (who makes the beer)
- `taps__venue__name` (what venue/venues has/have it on tap)
- `style__name` (what specific style, e.g. American IPA)
- `style__category__name` (what style categor, e.g. IPA)

You can also attach specific lookups to narrow/widen your search:

- For numeric fields:
   - (Nothing appended): exact match
   - `__lte`: less than or equal to
   - `__gte`: greater than or equal to
   - `__lt`: less than
   - `__gt`: greater than
   - `__isnull`: boolean (give a value of `True` or `False`)
   - `__in`: comma-separated list of values
- For string fields:
   - (Nothing appended): exact match
   - `__iexact`: case-insensitive exact match
   - `__icontains`: case-insensitive contains
   - `__istartswith`: case-insensitive starts with
   - `__iendswith`: case-insensitive ends with
   - `__startswith`: case-sensitive starts with
   - `__endswith`: case-sensitive ends with
   - `__contains`: case-sensitive contains
   - `__regex`: matches case-sensitive regex
   - `__iregex`: matches case-insensitive regex
   - `__isnull`: boolean (give a value of `True` or `False`)
   - `__in`: comma-separated list of values


To do the filtering, simply GET
`/beers/?name__icontains=monkey&taps__venue__name__icontains=straight`
