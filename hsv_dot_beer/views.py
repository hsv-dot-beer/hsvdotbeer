from django.shortcuts import redirect, render
from venues.models import Venue


def home(request):
    if request.user.is_anonymous:
        # redirect anonymous users to the browseable API
        return redirect("api-root")
    if request.user.is_superuser:
        venues_managed = Venue.objects.order_by("name")
    else:
        venues_managed = list(request.user.venues_managed.order_by("name"))
        if len(venues_managed) == 1:
            return redirect("venue_table", args=[venues_managed[0].id])
    return render(request, "venues/venue-list.html", {"venues": venues_managed})
