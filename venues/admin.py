from django.contrib import admin

from . import models


class VenueAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


class VenueAPIConfigurationAdmin(admin.ModelAdmin):
    list_display = ("id", "venue")
    list_select_related = ("venue",)


class VenueTapManagerAdmin(admin.ModelAdmin):
    list_display = ("id", "venue", "user")
    list_select_related = ("venue", "user")


admin.site.register(models.Venue, VenueAdmin)
admin.site.register(models.VenueAPIConfiguration, VenueAPIConfigurationAdmin)
admin.site.register(models.VenueTapManager, VenueTapManagerAdmin)
