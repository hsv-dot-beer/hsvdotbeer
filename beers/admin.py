from django.contrib import admin

from . import models

admin.site.register(models.BeerStyleCategory)
admin.site.register(models.BeerStyleTag)
admin.site.register(models.BeerStyle)
admin.site.register(models.Manufacturer)
