from django.conf import settings
from django.shortcuts import redirect, render
from venues.models import Venue


def home(request):
    if request.user.is_anonymous:
        if settings.IS_ALABAMA_DOT_BEER:
            return render(request, "hsv_dot_beer/alabama_dot_beer.html")
        return render(request, "hsv_dot_beer/home.html")
    if request.user.is_superuser:
        venues_managed = Venue.objects.order_by("name")
    else:
        venues_managed = list(request.user.venues_managed.order_by("name"))
        if len(venues_managed) == 1:
            return redirect("venue_table", venue_id=venues_managed[0].id)
        if not venues_managed:
            if settings.IS_ALABAMA_DOT_BEER:
                return render(request, "hsv_dot_beer/alabama_dot_beer.html")
            return render(request, "hsv_dot_beer/home.html")
    return render(request, "venues/venue-list.html", {"venues": venues_managed})
