from django.contrib import admin, messages
from django.db import transaction

from . import models


class BeerAdmin(admin.ModelAdmin):

    def merge_beers(self, request, queryset):
        """
        Merge multiple beers into one.

        Takes the best guess as to which beer to keep based on these criteria:
        1. If one beer has a color and the others don't, keep it.
        2. If one beer has more *_url fields set than the others, keep it.
           In case of a tie, the beer that's on tap at more places is kept.
           In case that's tied, use lowest PK as a tiebreaker.
        3. If neither of the above is set, keep the one with the lowest PK.
        """
        beers = list(queryset)
        if len(beers) == 1:
            self.message_user(
                request,
                message='Nothing to do; you only selected one beer.',
            )
            return
        keeper = None
        beers_with_color = [
            i for i in beers if i.color_srm or i.color_html
        ]
        if len(beers_with_color) == 1:
            keeper = beers_with_color[0]
        else:
            fields = [
                i.name for i in beers[0]._meta.fields if i.name.endswith('_url')
            ]
            max_url_fields_set = -1
            most_places_on_tap = -1
            for beer in beers:
                fields_set = sum(
                    bool(getattr(beer, field)) for field in fields
                )
                if fields_set > max_url_fields_set:
                    max_url_fields_set = fields_set
                    keeper = beer
                    most_places_on_tap = beer.taps.count()
                elif fields_set == max_url_fields_set:
                    # use number of taps occupied as a tiebreaker
                    places_on_tap = beer.taps.count()
                    if places_on_tap > most_places_on_tap or (
                            places_on_tap == most_places_on_tap and
                            beer.id < keeper.id
                    ):
                        max_url_fields_set = fields_set
                        keeper = beer
                        most_places_on_tap = places_on_tap
        if not keeper:
            self.message_user(
                request,
                message='Unable to determine which beer to keep!',
                level=messages.ERROR,
            )
            return
        with transaction.atomic():
            for beer in beers:
                if beer == keeper:
                    continue
                keeper.merge_from(beer)
        self.message_user(
            request,
            message=f'Merged {", ".join(str(i) for i in beers if i != keeper)} into '
            f'{keeper}'
        )

    merge_beers.short_description = 'Merge beers'
    actions = ['merge_beers']
    list_display = ('name', 'manufacturer', 'id')
    list_filter = ('name', 'manufacturer')
    list_select_related = ('manufacturer', )
    search_fields = ('name', 'manufacturer__name')


admin.site.register(models.BeerStyleCategory)
admin.site.register(models.BeerStyleTag)
admin.site.register(models.BeerStyle)
admin.site.register(models.Manufacturer)
admin.site.register(models.BeerPrice)
admin.site.register(models.ServingSize)
admin.site.register(models.BeerAlternateName)
admin.site.register(models.ManufacturerAlternateName)
admin.site.register(models.Beer, BeerAdmin)
admin.site.register(models.UntappdMetadata)
