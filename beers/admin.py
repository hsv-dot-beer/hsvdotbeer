from django.contrib import admin

from . import models

admin.site.register(models.BeerStyleCategory)
admin.site.register(models.BeerStyleTag)
admin.site.register(models.BeerStyle)
admin.site.register(models.Manufacturer)
admin.site.register(models.BeerPrice)
admin.site.register(models.ServingSize)
admin.site.register(models.BeerAlternateName)
admin.site.register(models.ManufacturerAlternateName)
admin.site.register(models.Beer)
