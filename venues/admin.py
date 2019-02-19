from django.contrib import admin

from . import models


admin.site.register(models.Venue)
admin.site.register(models.VenueAPIConfiguration)
