# Venues

These are locations that serve beer/cider/mead/... via taps.

## Creating a venue

**Request**:

`POST` `/api/v1/venues/`

Parameters:

Name              | Type   | Required | Description
------------------|--------|----------|------------
name              | string | Yes      | A friendly name for the venue (e.g. Sneakers O'Toole's)
address           | string | No       | The street address of the venue
city              | string | No       | The city in which the venue is located
state             | string | No       | The state or province in which the venue is located
postal_code       | string | No       | The zip/postal code of the venue
website           | string | No       | Where to find the venue on the web
facebook_page     | string | No       | Where to find the venue on Facebook
twitter_handle    | string | No       | Where to find the venue on Twitter
instagram_handle  | string | No       | Where to find the venue on Instagram
tap_list_provider | string | No       | Who provides the venue's digital tap list (DigitalPour, TapHunter, Untappd, etc.)

**NOTE**: tap_list_provider is restricted to the following options:

- `"manual"` (The venue uses a chalkboard or other such manual means)
- `"digitalpour"` (DigitalPour)
- `"taphunter"` (TapHunter)
- `"untappd"` (Untappd)
- `""` (Unknown)
- `"nook_html"` (The Nook in Huntsville has its own static HTML tap list that requires scraping)

## Filtering

You can look up venues by the following fields:

- `name` (Venue name)
- `taps__beer__name` (Beer name)
- `taps__beer__style__name` (what specific style, e.g. American IPA)
- `taps__beer__style__category__name` (what style categor, e.g. IPA)

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
`/venues/?name__icontains=das+stahl&taps__beer__name__icontains=monkey`
