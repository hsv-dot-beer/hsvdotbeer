from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views

from beers.views import StyleMergeView
from .users.views import UserViewSet, UserCreateViewSet


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'users', UserCreateViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
    path('api/v1/venues/', include('venues.urls')),
    path('api/v1/events/', include('events.urls')),
    path('api/v1/beers/', include('beers.urls')),
    path('api/v1/taps/', include('taps.urls')),
    path('api-token-auth/', views.obtain_auth_token),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('', include('web.urls')),
    path('beers/mergestyles/', StyleMergeView.as_view()),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
