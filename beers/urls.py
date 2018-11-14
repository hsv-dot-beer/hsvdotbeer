from rest_framework.routers import DefaultRouter
from django.urls import include, path

from . import views

router = DefaultRouter()

router.register(r'styles', views.BeerStyleViewSet)
router.register(r'style-tags', views.BeerStyleTagViewSet)
router.register(r'categories', views.BeerStyleCategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
