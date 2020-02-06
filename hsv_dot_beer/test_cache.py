import os

from django_bmemcached.memcached import BMemcached, InvalidCacheOptions
from unittest.mock import patch
from hsv_dot_beer.config.production import get_cache
from django.test import TestCase


class CacheConfigTestCase(TestCase):

    def test_good(self):
        with patch.dict(
            os.environ,
            MEMCACHIER_SERVERS='foo',
            MEMCACHIER_USERNAME='bar',
            MEMCACHIER_PASSWORD='baz',
        ):
            cache_opts = get_cache()
        server = cache_opts['default']['LOCATION']
        params = cache_opts['default']
        self.assertIsNone(
            BMemcached(server=server, params=params).get('foo')
        )

    def test_bad(self):
        with patch.dict(
            os.environ,
            MEMCACHIER_SERVERS='foo',
            MEMCACHIER_USERNAME='bar',
            MEMCACHIER_PASSWORD='baz',
        ):
            cache_opts = get_cache()
        server = cache_opts['default']['LOCATION']
        params = cache_opts['default']
        params['OPTIONS']['bogus key'] = 'spam'
        self.assertRaises(
            InvalidCacheOptions,
            BMemcached(server=server, params=params).get,
            'foo'
        )
