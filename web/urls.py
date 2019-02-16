from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^$', main_page, name='main_page'),
]

