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


## Moderation

Have you spotted two beers which should be merged into one?

Well you're in luck!

Simply fill out this HTTP request:

`POST /api/v1/beers/<pk>/mergefrom/` (replace `<pk>` with the ID of the beer
you want to **keep**, described below as "kept beer")

Body:

```json
{"id": 123}
```

Replace 123 with the ID of the beer you want to get rid of (described below as
"other beer")

The process:

1. All taps assigned to the other beer are assigned to the kept beer.
2. All fields which are unset (i.e. null or zero) on the kept beer and are
   set on the other beer will have their values copied over to the kept beer.
3. All fields which are set on the kept beer are untouched.

Example:

- Beer ID 123
   - Name: "Hoptastic IPA"
   - Manufacturer: "Drew's Basement Brewery"
   - IBU: 73
   - ABV: 5.7
   - Manufacturer URL: http://example.com/beer/Hoptastic
- Beer ID 456
   - Name: "Hoptastic"
   - Manufacturer: "Drew's Basement"
   - IBU: 75
   - ABV: 6
   - Color: `#abcdef`
   - Untappd URL: http://untappd.example.com/beer/122334

Request:

`POST /api/v1/beers/123/mergefrom/`

Body:
```json
{"id": 456}
```

Result:

- Beer 456 is deleted
- Taps assigned to 456 are moved to 123
- Fields copied to 123:
   - Color
   - Untappd URL
- Fields left alone on 123:
   - ABV
   - IBU
   - Manufacturer
