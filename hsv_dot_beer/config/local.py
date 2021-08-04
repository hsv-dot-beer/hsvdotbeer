import os
from .common import Common

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Local(Common):
    DEBUG = True

    # Mail
    EMAIL_HOST = "localhost"
    EMAIL_PORT = 1025
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    # CORS!
    CORS_ORIGIN_WHITELIST = ("https://localhost:8000",)

    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
