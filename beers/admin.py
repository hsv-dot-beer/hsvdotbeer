from csv import writer

from django.contrib import admin
from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect

from . import models


class BeerAlternateNameInline(admin.TabularInline):
    model = models.BeerAlternateName


class BeerAdmin(admin.ModelAdmin):

    def export_as_csv(self, request, queryset):
        queryset = queryset.select_related(
            'manufacturer', 'style',
        ).annotate(taps_count=Count('taps')).prefetch_related(
            'alternate_names',
        ).order_by(
            'manufacturer__name', 'name',
        )
        field_names = {
            'ID': 'id',
            'Name': 'name',
            'Manufacturer': 'manufacturer',
            'Style': 'style',
            'Taps occupied': 'taps_count',
        }
        most_alt_names = max(len(i.alternate_names.all()) for i in queryset)
        header = list(field_names.keys()) + [
            'Alternate Names',
        ] + ([''] * (most_alt_names - 1))

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(
            queryset.model._meta)
        csv_writer = writer(response)

        csv_writer.writerow(header)
        for obj in queryset:
            alt_names = [i.name for i in obj.alternate_names.all()]
            padding = [''] * (most_alt_names - len(alt_names))
            csv_writer.writerow(
                [
                    getattr(obj, val) if val in {'id', 'taps_count'}
                    else str(getattr(obj, val)) for val in field_names.values()
                ] + alt_names + padding,
            )
        return response

    def merge_beers(self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(
            f"/beers/mergebeers/?ids={','.join(selected)}",
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        fields = {
            'style': models.Style.objects.order_by('name'),
            'manufacturer': models.Manufacturer.objects.order_by('name'),
        }
        order_qs = fields.get(db_field.name)
        print(db_field.name, order_qs is not None)
        if order_qs:
            kwargs['queryset'] = order_qs

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    merge_beers.short_description = 'Merge beers'
    export_as_csv.short_description = 'Export as CSV'
    actions = ['merge_beers', 'export_as_csv']
    list_display = ('name', 'manufacturer', 'style', 'id')
    list_filter = ('manufacturer', 'style')
    list_select_related = ('manufacturer', 'style')
    search_fields = ('name', 'manufacturer__name', 'style__name')
    inlines = [BeerAlternateNameInline]


class ManufacturerAlternateNameInline(admin.TabularInline):
    model = models.ManufacturerAlternateName


class ManufacturerAdmin(admin.ModelAdmin):

    def url_fields_set(self, manufacturer):
        fields = [
            i.name
            for i in manufacturer._meta.fields
            if i.name.endswith('_url')
        ]
        return sum(
            bool(
                getattr(manufacturer, field)
            ) for field in fields
        )

    def merge_manufacturers(self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(
            f"/manufacturers/merge/?ids={','.join(selected)}",
        )

    inlines = [ManufacturerAlternateNameInline]
    merge_manufacturers.short_description = 'Merge manufacturers'
    actions = ['merge_manufacturers']
    list_display = ('name', 'id')
    list_filter = ('name', )
    search_fields = ('name', )


class BeerAlternateNameAdmin(admin.ModelAdmin):
    list_display = ('name', 'beer', 'id')
    list_select_related = ('beer', 'beer__manufacturer')
    list_filter = ('beer__name', 'beer__manufacturer__name')
    search_fields = ('name', 'beer__name', 'beer__manufacturer__name')


class ManufacturerAlternateNameAdmin(admin.ModelAdmin):
    list_display = ('name', 'manufacturer')
    list_select_related = ('manufacturer', )
    search_fields = ('name', 'manufacturer__name')


class BeerPriceAdmin(admin.ModelAdmin):
    list_display = ('beer', 'serving_size', 'venue', 'price', 'id')
    list_select_related = ('beer', 'venue', 'serving_size')
    search_fields = ('beer__name', 'serving_size__name', )


class StyleAlternateNameInline(admin.TabularInline):
    model = models.StyleAlternateName


class StyleAdmin(admin.ModelAdmin):
    inlines = [StyleAlternateNameInline]
    actions = ['export_as_csv', 'merge_styles']
    search_fields = ('name', 'alternate_names__name')
    list_display = ('name', 'id')

    def merge_styles(self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(
            f"/beers/mergestyles/?ids={','.join(selected)}",
        )

    def export_as_csv(self, request, queryset):
        queryset = queryset.prefetch_related(
            'alternate_names',
        ).annotate(names_count=Count('alternate_names__name'))
        meta = self.model._meta
        most_alt_names = max(i.names_count for i in queryset)
        field_names = [field.name for field in meta.fields]
        header = field_names + [
            'Alternate Names',
        ] + ([''] * (most_alt_names - 1))

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(
            meta)
        csv_writer = writer(response)

        csv_writer.writerow(header)
        for obj in queryset:
            alt_names = [i.name for i in obj.alternate_names.all()]
            padding = [''] * (most_alt_names - len(alt_names))
            csv_writer.writerow(
                [
                    getattr(obj, field) for field in field_names
                ] + alt_names + padding,
            )
        return response


admin.site.register(models.Style, StyleAdmin)
admin.site.register(models.Manufacturer, ManufacturerAdmin)
admin.site.register(models.BeerPrice, BeerPriceAdmin)
admin.site.register(models.ServingSize)
admin.site.register(models.BeerAlternateName, BeerAlternateNameAdmin)
admin.site.register(
    models.ManufacturerAlternateName, ManufacturerAlternateNameAdmin)
admin.site.register(models.Beer, BeerAdmin)
admin.site.register(models.UntappdMetadata)
