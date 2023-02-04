from csv import writer

from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect

from . import models


class BeerAdmin(admin.ModelAdmin):
    @admin.action(description="Export as CSV")
    def export_as_csv(self, request, queryset):
        queryset = (
            queryset.select_related(
                "manufacturer",
                "style",
            )
            .annotate(taps_count=Count("taps"))
            .order_by(
                "manufacturer__name",
                "name",
            )
        )
        field_names = {
            "ID": "id",
            "Name": "name",
            "Manufacturer": "manufacturer",
            "Style": "style",
            "Taps occupied": "taps_count",
            "Alternate Names": "alternate_names",
        }
        header = list(field_names.keys())

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename={}.csv".format(
            queryset.model._meta
        )
        csv_writer = writer(response)

        csv_writer.writerow(header)
        for obj in queryset:
            csv_writer.writerow(
                [
                    getattr(obj, val)
                    if val in {"id", "taps_count", "alternate_names"}
                    else str(getattr(obj, val))
                    for val in field_names.values()
                ]
            )
        return response

    @admin.action(description="Merge beers")
    def merge_beers(self, request, queryset):  # pylint: disable=unused-argument
        selected = request.POST.getlist(ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(
            f"/beers/mergebeers/?ids={','.join(selected)}",
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        fields = {
            "style": models.Style.objects.order_by("name"),
            "manufacturer": models.Manufacturer.objects.order_by("name"),
        }
        order_qs = fields.get(db_field.name)
        if order_qs:
            kwargs["queryset"] = order_qs

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    actions = ["merge_beers", "export_as_csv"]
    list_display = ("name", "manufacturer", "style", "id")
    list_filter = ("manufacturer", "style")
    list_select_related = ("manufacturer", "style")
    search_fields = ("name", "manufacturer__name", "style__name")


class ManufacturerAdmin(admin.ModelAdmin):
    def url_fields_set(self, manufacturer):
        fields = [i.name for i in manufacturer._meta.fields if i.name.endswith("_url")]
        return sum(bool(getattr(manufacturer, field)) for field in fields)

    @admin.action(description="Merge manufacturers")
    def merge_manufacturers(self, request, queryset):  # pylint: disable=unused-argument
        selected = request.POST.getlist(ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(
            f"/manufacturers/merge/?ids={','.join(selected)}",
        )

    actions = ["merge_manufacturers"]
    list_display = ("name", "id")
    list_filter = ("name",)
    search_fields = ("name",)


class BeerPriceAdmin(admin.ModelAdmin):
    list_display = ("beer", "serving_size", "venue", "price", "id")
    list_select_related = ("beer", "venue", "serving_size")
    search_fields = (
        "beer__name",
        "serving_size__name",
    )


class StyleAdmin(admin.ModelAdmin):
    actions = ["export_as_csv", "merge_styles"]
    search_fields = ("name", "alternate_names")
    list_display = ("name", "id")

    def merge_styles(self, request, queryset):  # pylint: disable=unused-argument
        selected = request.POST.getlist(ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(
            f"/beers/mergestyles/?ids={','.join(selected)}",
        )

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        queryset = list(queryset)
        field_names = [field.name for field in meta.fields]
        header = field_names

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={meta}.csv"
        csv_writer = writer(response)

        csv_writer.writerow(header)
        for obj in queryset:
            csv_writer.writerow([getattr(obj, field) for field in field_names])
        return response


admin.site.register(models.Style, StyleAdmin)
admin.site.register(models.Manufacturer, ManufacturerAdmin)
admin.site.register(models.BeerPrice, BeerPriceAdmin)
admin.site.register(models.ServingSize)
admin.site.register(models.Beer, BeerAdmin)
admin.site.register(models.UntappdMetadata)
