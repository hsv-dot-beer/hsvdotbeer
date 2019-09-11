import os
from .common import Common
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Local(Common):
    DEBUG = True

    # Testing
    INSTALLED_APPS = Common.INSTALLED_APPS
    INSTALLED_APPS += ('django_nose',)
    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
    NOSE_ARGS = [
        os.path.dirname(BASE_DIR),
        '--with-coverage',
        '--with-progressive',
        '--cover-package=hsv_dot_beer',
        '--cover-package=venues',
        '--cover-package=beers',
        '--cover-package=tap_list_providers',
    ]

    # Mail
    EMAIL_HOST = 'localhost'
    EMAIL_PORT = 1025
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    # CORS!
    CORS_ORIGIN_WHITELIST = (
        'https://localhost:8000',
    )

    CACHES = {
      'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
      }
    }
