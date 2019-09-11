import os
from .common import Common


def get_cache():
    try:
        servers = os.environ['MEMCACHIER_SERVERS']
        username = os.environ['MEMCACHIER_USERNAME']
        password = os.environ['MEMCACHIER_PASSWORD']
    except KeyError:
        return {
          'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
          }
        }
    return {
      'default': {
        'BACKEND': 'django_bmemcached.memcached.BMemcached',
        # TIMEOUT is not the connection timeout! It's the default
        # expiration
        # timeout that should be applied to keys! Setting it to `None`
        # disables expiration.
        'TIMEOUT': None,
        'LOCATION': servers,
        'OPTIONS': {
          'binary': True,
          'username': username,
          'password': password,
          'behaviors': {
            # Enable faster IO
            'no_block': True,
            'tcp_nodelay': True,
            # Keep connection alive
            'tcp_keepalive': True,
            # Timeout settings
            'connect_timeout': 2000,  # ms
            'send_timeout': 750 * 1000,  # us
            'receive_timeout': 750 * 1000,  # us
            '_poll_timeout': 2000,  # ms
            # Better failover
            'ketama': True,
            'remove_failed': 1,
            'retry_timeout': 2,
            'dead_timeout': 30,
          }
        }
      }
    }


class Production(Common):
    INSTALLED_APPS = Common.INSTALLED_APPS
    SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
    # Site
    # https://docs.djangoproject.com/en/2.0/ref/settings/#allowed-hosts
    ALLOWED_HOSTS = ["*"]
    INSTALLED_APPS += ("gunicorn", )

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/2.0/howto/static-files/
    # http://django-storages.readthedocs.org/en/latest/index.html
    INSTALLED_APPS += ('storages',)
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = os.getenv('DJANGO_AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('DJANGO_AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('DJANGO_AWS_STORAGE_BUCKET_NAME')
    AWS_DEFAULT_ACL = 'public-read'
    AWS_AUTO_CREATE_BUCKET = True
    AWS_QUERYSTRING_AUTH = False
    MEDIA_URL = f'https://s3.amazonaws.com/{AWS_STORAGE_BUCKET_NAME}/'

    # noqa
    # https://developers.google.com/web/fundamentals/performance/optimizing-content-efficiency/http-caching#cache-control
    # Response can be cached by browser and any intermediary caches (i.e. it is
    # "public") for up to 1 day
    # 86400 = (60 seconds x 60 minutes x 24 hours)
    AWS_HEADERS = {
        'Cache-Control': 'max-age=86400, s-maxage=86400, must-revalidate',
    }

    # cross-origin request sharing
    CORS_ORIGIN_WHITELIST = (
        'http://localhost:8000',
        'https://localhost:8000',
        'https://hsv.beer',
        'https://dev.hsv.beer',
        'https://nuxt.hsv.beer',
    )

    CORS_ORIGIN_REGEX_WHITELIST = [
        # while we're developing the nuxt.js frontend, heroku PR review apps
        # are deployed at https://hsvdotbeer-nuxt-pr-NNN.herokuapp.com
        r"^https:\/\/hsvdotbeer-nuxt-pr-\d+\.herokuapp\.com$",
    ]

    SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

    CACHES = get_cache()
