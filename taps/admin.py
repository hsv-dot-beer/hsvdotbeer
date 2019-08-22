from django.contrib import admin

from . import models


class TapAdmin(admin.ModelAdmin):

    list_display = ('tap_number', 'venue', 'beer', 'id')
    list_filter = ('venue', )
    list_select_related = ('venue', 'beer')
    search_fields = ('beer__name', 'venue__name', 'beer__manufacturer__name')


admin.site.register(models.Tap, TapAdmin)
