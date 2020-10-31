from django.conf import settings
from django.http import HttpRequest


def add_al_dot_beer_to_context(request: HttpRequest):
    return {"alabama_dot_beer": settings.IS_ALABAMA_DOT_BEER}
