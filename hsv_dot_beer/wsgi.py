"""
WSGI config for viral project.
It exposes the WSGI callable as a module-level variable named ``application``.
For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/gunicorn/
"""
import json
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hsv_dot_beer.config')
os.environ.setdefault('DJANGO_CONFIGURATION', 'Production')

from configurations.wsgi import get_wsgi_application  # noqa


class CloudflareProxy(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        cf_visitor = environ.get('HTTP_CF_VISITOR')
        if cf_visitor:
            try:
                cf_visitor = json.loads(cf_visitor)
            except ValueError:
                pass
            else:
                proto = cf_visitor.get('scheme')
                if proto is not None:
                    environ['wsgi.url_scheme'] = proto
        return self.app(environ, start_response)


application = CloudflareProxy(get_wsgi_application())
