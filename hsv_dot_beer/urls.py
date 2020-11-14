from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views

from beers.views import (
    StyleMergeView,
    BeerMergeView,
    ManufacturerMergeView,
    beer_form,
    style_form,
)
from taps.views import (
    tap_form,
    manufacturer_select_for_form,
    save_tap_form,
    clear_tap,
    undo_clear,
)
from venues.views import venue_table
from .users.views import UserViewSet, UserCreateViewSet
from .views import home


router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"users", UserCreateViewSet)

urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
    path("beeradmin/", admin.site.urls),
    path("api/v1/", include(router.urls)),
    path("api/v1/venues/", include("venues.urls")),
    path("api/v1/events/", include("events.urls")),
    path("api/v1/beers/", include("beers.urls")),
    path("api/v1/taps/", include("taps.urls")),
    path("api-token-auth/", views.obtain_auth_token),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("beers/mergestyles/", StyleMergeView.as_view()),
    path("beers/mergebeers/", BeerMergeView.as_view()),
    path("beers/", beer_form, name="create_beer"),
    path("beers/<int:beer_id>/", beer_form, name="edit_beer"),
    path("manufacturers/merge/", ManufacturerMergeView.as_view()),
    path("styles/", style_form, name="create_style"),
    path("styles/<int:style_id>/", style_form, name="edit_style"),
    path(
        "venues/<int:venue_id>/taps/select-manufacturer/<int:tap_number>/",
        manufacturer_select_for_form,
        name="edit_tap_pick_mfg",
    ),
    path(
        "venues/<int:venue_id>/taps/select-manufacturer/",
        manufacturer_select_for_form,
        name="create_tap_pick_mfg",
    ),
    path("venues/<int:venue_id>/taps/<int:tap_number>/", tap_form, name="edit_tap"),
    path("venues/<int:venue_id>/taps/", tap_form, name="create_tap"),
    path(
        "venues/<int:venue_id>/taps/<int:tap_number>/save/",
        save_tap_form,
        name="edit_tap_save",
    ),
    path("venues/<int:venue_id>/", venue_table, name="venue_table"),
    path("taps/<int:tap_id>/clear/", clear_tap, name="clear_tap"),
    path("taps/<int:tap_id>/clear/undo/<int:beer_id>/", undo_clear, name="undo_clear"),
    path("", home),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
