"""Tap views"""
import datetime

from rest_framework.viewsets import ModelViewSet
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.db.models import Max, Prefetch
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.utils.html import format_html
from django.utils.http import urlencode
from django.utils.timezone import now

from beers.forms import ManufacturerSelectForm
from venues.models import Venue, VenueTapManager
from . import serializers
from . import models
from . import forms


class TapViewSet(ModelViewSet):
    serializer_class = serializers.TapSerializer
    queryset = models.Tap.objects.select_related("venue").order_by("id")


@login_required
def manufacturer_select_for_form(request, venue_id: int, tap_number: int = None):
    venue_qs = Venue.objects.prefetch_related(
        Prefetch(
            "venue_tap_managers",
            queryset=VenueTapManager.objects.filter(user=request.user).select_related(
                "default_manufacturer",
            ),
        )
    )
    if request.user.is_superuser:
        venue = get_object_or_404(venue_qs, id=venue_id)
    else:
        venue = get_object_or_404(
            venue_qs.filter(venue_tap_managers__user=request.user),
            id=venue_id,
        )

    try:
        manager = venue.venue_tap_managers.all()[0]
    except IndexError:
        # must be a super user
        default_manufacturer = None
    else:
        default_manufacturer = manager.default_manufacturer
    if default_manufacturer:
        form = ManufacturerSelectForm(initial={"manufacturer": default_manufacturer.id})
    else:
        form = ManufacturerSelectForm()
    return render(
        request,
        "beers/manufacturer-select.html",
        context={"form": form, "venue": venue, "tap_number": tap_number},
    )


@login_required
def tap_form(request, venue_id: int, tap_number: int = None):
    """Simple form for creating taps"""
    if request.user.is_superuser:
        venue = get_object_or_404(Venue, id=venue_id)
    else:
        venue = get_object_or_404(
            Venue.objects.prefetch_related("managers").filter(
                managers=request.user,
            ),
            id=venue_id,
        )
    if request.method != "POST":
        return HttpResponseNotAllowed("You have to POST here")
    form = ManufacturerSelectForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "beers/manufacturer-select.html",
            context={"form": form, "venue": venue, "tap_number": tap_number},
            status=400,
        )
    manufacturer = form.cleaned_data["manufacturer"]

    if tap_number:
        tap = get_object_or_404(models.Tap, venue=venue, tap_number=tap_number)
        form = forms.TapForm(
            instance=tap,
            manufacturer=manufacturer,
        )
    else:
        try:
            new_tap_number = (
                models.Tap.objects.filter(venue=venue).aggregate(
                    max_tap=Max("tap_number")
                )["max_tap"]
                + 1
            )
        except TypeError:
            new_tap_number = 1
        tap = models.Tap(venue=venue, tap_number=new_tap_number)
        form = forms.TapForm(instance=tap, manufacturer=manufacturer)

    return render(
        request,
        "taps/tap_form.html",
        {"form": form, "tap": tap, "venue": venue},
    )


@login_required
def save_tap_form(request, venue_id: int, tap_number: int):
    timestamp = now()
    if request.method != "POST":
        return HttpResponseNotAllowed("Only POSTs allowed here")
    with transaction.atomic():
        if request.user.is_superuser:
            venue = get_object_or_404(Venue, id=venue_id)
        else:
            venue = get_object_or_404(
                Venue.objects.prefetch_related("managers").filter(
                    managers=request.user,
                ),
                id=venue_id,
            )
        try:
            tap = models.Tap.objects.select_related("beer").get(
                venue=venue, tap_number=tap_number
            )
        except models.Tap.DoesNotExist:
            tap = models.Tap(venue=venue, tap_number=tap_number)
        original_beer_id = tap.beer_id
        original_beer = tap.beer
        form = forms.TapForm(request.POST, instance=tap)
        if form.is_valid():
            if (
                form.cleaned_data.get("beer")
                and original_beer_id != form.cleaned_data["beer"].id
            ):
                tap.time_added = timestamp
            tap.time_updated = timestamp
            tap = form.save()
            tap.venue.tap_list_last_update_time = timestamp
            tap.venue.tap_list_last_check_time = timestamp
            tap.venue.save()
        else:
            return render(
                request,
                "taps/tap_form.html",
                {"form": form, "tap": tap, "venue": venue},
                status=400,
            )
    if tap.beer:
        messages.add_message(
            request,
            messages.SUCCESS,
            f"Successfully saved {tap.beer} on tap {tap.tap_number}",
        )
    elif original_beer:
        messages.add_message(
            request,
            messages.SUCCESS,
            f"Successfully removed {original_beer} from tap {tap.tap_number}",
        )
    else:
        messages.add_message(
            request,
            messages.SUCCESS,
            f"Successfully did... nothing on tap {tap.tap_number}",
        )
    return redirect(reverse("venue_table", args=[venue.id]))


@login_required
def clear_tap(request, tap_id: int):
    """Clear the beer assigned to a tap"""
    queryset = models.Tap.objects.select_related("beer")
    if not request.user.is_superuser:
        queryset = queryset.filter(venue__managers=request.user)
    tap = get_object_or_404(queryset, id=tap_id)
    if not tap.beer:
        messages.add_message(
            request,
            messages.SUCCESS,
            f"There was no beer assigned to tap {tap.tap_number}. Carry on.",
        )
    else:
        old_beer = tap.beer
        undo_url = reverse("undo_clear", args=[tap.id, old_beer.id])
        query_args = {}
        if tap.estimated_percent_remaining:
            query_args["percent_remaining"] = tap.estimated_percent_remaining
        tap.estimated_percent_remaining = None
        if tap.gas_type:
            query_args["gas_type"] = tap.gas_type
        tap.gas_type = ""
        if tap.time_added:
            query_args["time_added"] = tap.time_added.isoformat()
        tap.time_added = now()
        if tap.time_updated:
            query_args["time_updated"] = tap.time_updated.isoformat()
        if query_args:
            undo_url = f"{undo_url}?{urlencode(query_args)}"
        tap.beer = None
        tap.save()
        button_css = (
            "inline-block text-sm px-4 py-2 leading-none border rounded text-white"
            "border-blue-600 bg-blue-600 hover:border-blue-600 hover:text-black "
            "hover:bg-white mt-4 lg:mt-0"
        )
        messages.add_message(
            request,
            messages.SUCCESS,
            format_html(
                'Successfully removed {old_beer} from tap {tap_number}. <a href="{url}"'
                ' class="{button_css}">Undo</a>',
                old_beer=old_beer,
                tap_number=tap.tap_number,
                url=undo_url,
                button_css=button_css,
            ),
        )
    return redirect(reverse("venue_table", args=[tap.venue_id]))


@login_required
def undo_clear(request, tap_id: int, beer_id: int):
    """Quickly undo clearing a beer"""
    queryset = models.Tap.objects.select_related("beer").filter(beer=None)
    if not request.user.is_superuser:
        queryset = queryset.filter(venue__managers=request.user)
    tap = get_object_or_404(queryset, id=tap_id)
    tap.beer_id = beer_id
    if percent_remaining := request.GET.get("percent_remaining"):
        tap.estimated_percent_remaining = percent_remaining
    if gas_type := request.GET.get("gas_type"):
        tap.gas_type = gas_type
    if time_added := request.GET.get("time_added"):
        tap.time_added = datetime.datetime.fromisoformat(time_added)
    if time_updated := request.GET.get("time_updated"):
        tap.time_updated = datetime.datetime.fromisoformat(time_updated)
    tap.save()
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Successfully reattached {tap.beer} to tap {tap.tap_number}.",
    )
    return redirect(reverse("venue_table", args=[tap.venue_id]))
