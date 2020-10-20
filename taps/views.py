from rest_framework.viewsets import ModelViewSet
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Max
from django.contrib.auth.decorators import login_required

from venues.models import Venue
from . import serializers
from . import models
from . import forms


class TapViewSet(ModelViewSet):
    serializer_class = serializers.TapSerializer
    queryset = models.Tap.objects.select_related("venue").order_by("id")


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

    if request.method == "POST":
        if tap_number:
            form = forms.TapForm(
                request.POST,
                instance=get_object_or_404(
                    models.Tap, venue=venue, tap_number=tap_number
                ),
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
            form = forms.TapForm(
                request.POST,
                instance=models.Tap(venue=venue, tap_number=new_tap_number),
            )
        if form.is_valid():
            tap = form.save()
            return redirect("edit_tap", tap_id=tap.id)
        else:
            tap = None
    else:
        if tap_number:
            tap = get_object_or_404(models.Tap, venue=venue, tap_number=tap_number)
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
            print("new tap", new_tap_number)
            tap = models.Tap(venue=venue, tap_number=new_tap_number)
        form = forms.TapForm(instance=tap)

    return render(
        request, "taps/tap_form.html", {"form": form, "tap": tap, "venue": venue}
    )
