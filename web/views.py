"""Views for web frontend"""
from django.template.loader import get_template
from django.http import HttpResponse

from taps.models import Tap


def main_page(request):
    template = get_template('index.html')
    html = template.render({
        'tap_count': Tap.objects.filter(beer__isnull=False).count(),
    })
    return HttpResponse(html)
