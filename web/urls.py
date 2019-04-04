from django.conf.urls import url
from .views import main_page

urlpatterns = [
        url(r'^$', main_page, name='main_page'),
]
