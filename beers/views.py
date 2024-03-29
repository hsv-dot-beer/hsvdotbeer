"""Beer views"""
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.utils import IntegrityError
from django.db.models import Prefetch, Count, Max
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404 as dj_get_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404

from taps.models import Tap
from venues.serializers import VenueSerializer
from venues.models import Venue
from venues.filters import VenueFilterSet

from . import serializers
from . import models
from . import filters
from . import forms


class CachedListMixin:
    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ModerationMixin:
    @action(detail=True, methods=["POST"])
    def mergefrom(self, request, pk):
        serializer = serializers.OtherPKSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = get_object_or_404(self.get_queryset(), id=pk)
        model = self.get_queryset().model
        try:
            other = self.get_queryset().get(id=serializer.validated_data["id"])
        except model.DoesNotExist:
            raise serializers.serializers.ValidationError(
                {
                    "id": [
                        f"A {model.__name__} with the given ID does not exist.",
                    ],
                }
            )
        instance.merge_from(other)
        instance.refresh_from_db()
        return Response(self.get_serializer(instance=instance).data)


class ManufacturerViewSet(CachedListMixin, ModerationMixin, ModelViewSet):
    serializer_class = serializers.ManufacturerSerializer
    queryset = models.Manufacturer.objects.order_by("name")


class BeerViewSet(CachedListMixin, ModerationMixin, ModelViewSet):
    serializer_class = serializers.BeerSerializer
    queryset = (
        models.Beer.objects.select_related(
            "manufacturer",
            "style",
            "untappd_metadata",
            "style",
        )
        .prefetch_related(
            Prefetch(
                "taps",
                queryset=Tap.objects.select_related(
                    "venue",
                ),
            ),
            Prefetch(
                "prices",
                queryset=models.BeerPrice.objects.select_related(
                    "venue",
                    "serving_size",
                ),
            ),
        )
        .annotate(
            most_recently_added=Max("taps__time_added"),
        )
        .order_by("manufacturer__name", "name")
    )
    filterset_class = filters.BeerFilterSet

    @method_decorator(cache_page(60 * 5))
    @action(detail=True, methods=["GET"])
    def placesavailable(self, request, pk):
        """Get all the venues at which the given beer is on tap"""
        queryset = (
            Venue.objects.filter(taps__beer__id=pk)
            .distinct()
            .order_by(
                "name",
            )
        )
        # let the user use all the venue filters just for kicks
        queryset = VenueFilterSet(request.query_params, queryset=queryset).qs

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = VenueSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = VenueSerializer(queryset, many=True)
        return Response(serializer.data)

    @method_decorator(cache_page(60 * 5))
    @action(detail=False, methods=["GET"])
    def autocomplete(self, request):
        """Attempt to autocomplete beers"""
        try:
            search_term = request.GET["search"].lower()
            if not search_term:
                raise KeyError(search_term)
        except KeyError:
            return Response(
                {
                    "error": 'You must specify "search" as a query argument',
                }
            )
        beer_qs = (
            models.Beer.objects.filter(name__icontains=search_term)
            .select_related("manufacturer")
            .annotate(
                taps_count=Count("taps", distinct=True),
            )
            .values(
                "name",
                "taps_count",
                "id",
                "manufacturer__name",
                "alternate_names",
            )
            .order_by("-taps_count", "manufacturer__name", "name", "id")[:10]
        )
        mfg_qs = (
            models.Manufacturer.objects.filter(
                name__icontains=search_term,
            )
            .annotate(
                beers_count=Count("beers", distinct=True),
                taps_occupied=Count("beers__taps", distinct=True),
            )
            .values(
                "name",
                "beers_count",
                "id",
                "taps_occupied",
                "alternate_names",
            )
            .order_by("-taps_occupied", "-beers_count", "name")[:10]
        )
        style_qs = (
            models.Style.objects.filter(
                name__contains=search_term,
            )
            .annotate(
                beers_count=Count("beers", distinct=True),
                taps_occupied=Count("beers__taps", distinct=True),
            )
            .values(
                "name",
                "beers_count",
                "id",
                "taps_occupied",
                "alternate_names",
            )
            .order_by("-taps_occupied", "-beers_count", "name")[:10]
        )
        alt_beers = {i["id"]: i["alternate_names"] for i in beer_qs}
        alt_mfgs = {i["id"]: i["alternate_names"] for i in mfg_qs}
        alt_styles = {i["id"]: i["alternate_names"] for i in style_qs}
        result = {
            "beers": [
                {
                    "name": i["name"],
                    "taps": i["taps_count"],
                    "alternate_names": alt_beers.get(i["id"], []),
                    "manufacturer": i["manufacturer__name"],
                }
                for i in beer_qs
            ],
            "styles": [
                {
                    "name": i["name"],
                    "beers": i["beers_count"],
                    "taps_occupied": i["taps_occupied"],
                    "alternate_names": alt_styles.get(i["id"], []),
                }
                for i in style_qs
            ],
            "manufacturers": [
                {
                    "name": i["name"],
                    "beers": i["beers_count"],
                    "taps_occupied": i["taps_occupied"],
                    "alternate_names": alt_mfgs.get(i["id"], []),
                }
                for i in mfg_qs
            ],
        }
        return Response(result)


class StyleMergeView(TemplateView):
    def get(self, request):
        user = request.user
        if not user.is_staff:
            return redirect(f'/{reverse("admin:login")}/?next={request.path}')
        if "ids" not in request.GET:
            return HttpResponse("you must specify IDs", status=400)
        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["styles"] = models.Style.objects.filter(
            id__in=context["view"].request.GET["ids"].split(","),
        )
        context["back_link"] = reverse("admin:beers_style_changelist")

        return context

    def post(self, request):
        try:
            all_pks = [int(i) for i in request.POST["all-styles"].split(",")]
            kept_pk = int(request.POST["styles"])
        except (KeyError, ValueError):
            return HttpResponse("Invalid data received!", status=400)
        styles = models.Style.objects.filter(id__in=all_pks).prefetch_related(
            "beers",
        )
        try:
            desired_style = [i for i in styles if i.id == kept_pk][0]
        except IndexError:
            return HttpResponse(
                "Chosen style was not part of the list!",
                status=400,
            )
        try:
            desired_style.merge_from(styles)
        except IntegrityError:
            return HttpResponse(
                "At least one of the beers has an alternate name that " "conflicts",
                status=400,
            )
        except ValueError as exc:
            return HttpResponse(str(exc), status=400)
        return redirect(reverse("admin:beers_style_changelist"))

    template_name = "beers/merge_styles.html"


class BeerMergeView(TemplateView):
    def get(self, request):
        user = request.user
        if not user.is_staff:
            return redirect(f'/{reverse("admin:login")}/?next={request.path}')
        if "ids" not in request.GET:
            return HttpResponse("you must specify IDs", status=400)
        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["beers"] = models.Beer.objects.filter(
            id__in=context["view"].request.GET["ids"].split(","),
        ).select_related("manufacturer")
        context["back_link"] = reverse("admin:beers_beer_changelist")

        return context

    def post(self, request):
        try:
            all_pks = [int(i) for i in request.POST["all-beers"].split(",")]
            kept_pk = int(request.POST["beers"])
        except (KeyError, ValueError):
            return HttpResponse("Invalid data received!", status=400)
        beers = models.Beer.objects.filter(id__in=all_pks).prefetch_related(
            "taps",
        )
        try:
            desired_beer = [i for i in beers if i.id == kept_pk][0]
        except IndexError:
            return HttpResponse(
                "Chosen beer was not part of the list!",
                status=400,
            )
        try:
            with transaction.atomic():
                for beer in beers:
                    if beer != desired_beer:
                        desired_beer.merge_from(beer)
        except IntegrityError:
            return HttpResponse(
                "At least one of the beers has an alternate name that " "conflicts",
                status=400,
            )
        except ValueError as exc:
            return HttpResponse(str(exc), status=400)
        return redirect(reverse("admin:beers_beer_changelist"))

    template_name = "beers/merge_beers.html"


class ManufacturerMergeView(TemplateView):
    def get(self, request):
        user = request.user
        if not user.is_staff:
            return redirect(f'/{reverse("admin:login")}/?next={request.path}')
        if "ids" not in request.GET:
            return HttpResponse("you must specify IDs", status=400)
        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["manufacturers"] = models.Manufacturer.objects.filter(
            id__in=context["view"].request.GET["ids"].split(","),
        )
        context["back_link"] = reverse("admin:beers_manufacturer_changelist")

        return context

    def post(self, request):
        try:
            all_pks = [int(i) for i in request.POST["all-manufacturers"].split(",")]
            kept_pk = int(request.POST["manufacturers"])
        except (KeyError, ValueError):
            return HttpResponse("Invalid data received!", status=400)
        manufacturers = models.Manufacturer.objects.filter(
            id__in=all_pks,
        )
        try:
            desired_manufacturer = [i for i in manufacturers if i.id == kept_pk][0]
        except IndexError:
            return HttpResponse(
                "Chosen manufacturer was not part of the list!",
                status=400,
            )
        try:
            with transaction.atomic():
                for manufacturer in manufacturers:
                    if manufacturer != desired_manufacturer:
                        desired_manufacturer.merge_from(manufacturer)
        except IntegrityError:
            return HttpResponse(
                "At least one of the beers has an alternate name that " "conflicts",
                status=400,
            )
        except ValueError as exc:
            return HttpResponse(str(exc), status=400)
        return redirect(reverse("admin:beers_manufacturer_changelist"))

    template_name = "beers/merge_manufacturers.html"


@login_required
def beer_form(request, beer_id=None):
    """Simple form for creating beers"""
    if request.method == "POST":
        if beer_id:
            form = forms.BeerForm(
                request.POST,
                instance=dj_get_or_404(models.Beer, id=beer_id),
            )
        else:
            form = forms.BeerForm(request.POST)
        if form.is_valid():
            beer = form.save()
            return redirect("edit_beer", beer_id=beer.id)
        else:
            beer = None
    else:
        beer = None
        if beer_id:
            beer = dj_get_or_404(models.Beer, id=beer_id)
        form = forms.BeerForm(instance=beer)

    return render(request, "beers/beer_form.html", {"form": form, "beer": beer})


@login_required
def style_form(request, style_id=None):
    """Simple form for creating styles"""
    if request.method == "POST":
        if style_id:
            form = forms.StyleForm(
                request.POST,
                instance=dj_get_or_404(models.Style, id=style_id),
            )
        else:
            form = forms.StyleForm(request.POST)
        if form.is_valid():
            style = form.save()
            return redirect("edit_style", style_id=style.id)
        else:
            style = None
    else:
        style = None
        if style_id:
            style = dj_get_or_404(models.Style, id=style_id)
        form = forms.StyleForm(instance=style)

    return render(request, "beers/style_form.html", {"form": form, "style": style})
