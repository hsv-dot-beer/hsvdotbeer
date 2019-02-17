# Parsers

## What are these?

Parsers are a way of taking the data provided by the various API providers and
converting them into our format. Some are user-friendly (e.g. they give us
raw JSON), but some are not so nice (HTML embedded within a JS object).

## How does this work?

All parsers inherit from the BaseTapListProvider class in
`tap_list_providers/base.py`.

To make your own, you need to:

1. Declare a string that identifies your provider, e.g. `mybeer`.
2. In `venues/models.py`, edit the `TAP_LIST_PROVIDERS` attribute of the `Venue`
   class to add an entry for your provider in the form
   (`internal_name`, `Friendly display name`).
3. If necessary, add fields to the `VenueAPIConfiguration` model that detail
   what configuration data is required for your provider (URL, API key, etc.).
4. Create a migration for both of the above: `pipenv run ./manage.py makemigrations`
5. Create a file named after your provider in `tap_list_providers/parsers/`.
6. Your class should inherit from BaseTapListProvider and define the class-level
   (_not_ instance-level) attribute `provider_name`. That attribute must match
   the `internal_name` from step 2.
7. You need to implement the method `def handle_venue(self, venue)`. From there,
   iterate over the rooms in that venue and fill in data from what you get from
   the API provider.
8. Utilize the `get_beer` and `get_manufacturer` methods from the base class to
   simplify beer and manufacturer lookup, respectively. Those will automatically
   create the beers/manufacturers if no match is found (and eventually put them
   in a moderation queue).
9. If your provider has some sort of unique beer/manufacturer ID (or URL):
   1. Add that field to the beer/manufacturer model and create a migration for it.
   2. Create a migration for that new field.
   3. For beer fields, add that field to the `unique_fields` local variable in
      the `get_beer()` method of the base class.
   4. For manufacturer fields, either implement a spacial case as in the
      `if untappd_url` block of the `get_manufacturer()` method or (preferably)
      refactor the method to use the similar `unique_fields` logic as `get_beer()`
      and then update these docs accordingly.
10. Create a management command to parse all venues for your provider:
   1. Create a file called `parse<myprovider>.py` in `tap_list_providers/management/commands/`.
   2. Copy and paste the logic from one of the other files and change the
      references to refer to your code.
11. Save example data in `tap_list_providers/example_data`. This should be the
    same data you would get from making the HTTP call to get your data. This
    way you can use the `responses` library to fake the result of the HTTP call.
12. Create test code in `tap_list_providers/test/` that parses real data
    (calling the management command) and validates a few of the taps to make
    sure you get the right example data.
13. Schedule your task:
   1. Open http://localhost:8000/admin/ and under Periodic Tasks, select
   the `Add` link next to Periodic Tasks.
   2. Fields to fill in:
      - Name: `Parse <my provider>`
      - Task (registered): `tap_list_providers.tasks.parse_provider`
      - Description: `Update all venues from <my provider>`
      - Schedule block:
         - Crontab: click the green plus icon
            - Set minute to some value that is not currently used (0, 15, 30,
              45)
            - Leave the rest as defaults
            - Click Save
      - Click `show` next to `Arguments`.
      - Set the arguments block to `["internal_name"]` (double quotes are
        essential)
    3. Click `SAVE`
14. Export the updated schedule:
   ```bash
   pipenv run ./manage.py dumpdata --indent 2 -o tap_list_providers/fixtures/scheduled_tasks.json django_celery_beat.solarschedule django_celery_beat.periodictasks django_celery_beat.periodictask django_celery_beat.intervalschedule django_celery_beat.crontabschedule
   ```
15. Commit your changes and create a PR!
