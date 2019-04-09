from rest_framework.routers import DefaultRouter
from django.urls import include, path

from . import views

router = DefaultRouter()

router.register(r'styles', views.BeerStyleViewSet)
router.register(r'style-tags', views.BeerStyleTagViewSet)
router.register(r'categories', views.BeerStyleCategoryViewSet)
router.register(r'manufacturers', views.ManufacturerViewSet)
router.register(r'', views.BeerViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
