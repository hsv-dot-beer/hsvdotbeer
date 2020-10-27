from rest_framework.viewsets import ModelViewSet
from django.shortcuts import render, get_object_or_404
from django.db.models import Max, Prefetch
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed, HttpResponse
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
            venue_qs.filter(managers__user=request.user),
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
                managers__user=request.user,
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
        except KeyError:
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
                    managers__user=request.user,
                ),
                id=venue_id,
            )
        try:
            tap = models.Tap.objects.get(venue=venue, tap_number=tap_number)
        except models.Tap.DoesNotExist:
            tap = models.Tap(venue=venue, tap_number=tap_number)
        form = forms.TapForm(request.POST, instance=tap)
        if form.is_valid():
            if tap.beer_id != form.cleaned_data['beer'].id:
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
            )
    # TODO return to the redirect page
    return HttpResponse("Success! Will go to the venue page eventually")
