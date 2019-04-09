from rest_framework.routers import DefaultRouter
from django.urls import include, path

from . import views

router = DefaultRouter()

router.register(r'manufacturers', views.ManufacturerViewSet)
router.register(r'', views.BeerViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
