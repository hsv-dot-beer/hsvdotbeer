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
