from django.contrib import admin

from . import models


class VenueAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(models.Venue, VenueAdmin)
admin.site.register(models.VenueAPIConfiguration)
