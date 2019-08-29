#!/usr/bin/env python
"""Tasks for tap list providers"""

from json import JSONDecodeError
import logging

from requests.exceptions import RequestException
from celery import shared_task
from django.db import transaction
from django.db.models import Prefetch
from django.db.utils import OperationalError, IntegrityError

from venues.models import Venue
from taps.models import Tap
from tap_list_providers.base import BaseTapListProvider
# this import is needed for the subclass lookup to work
from tap_list_providers.parsers import (  # noqa
    digitalpour, taphunter, untappd, stemandstein, taplist_io,
)


LOG = logging.getLogger(__name__)


@shared_task(
    bind=False,
    autoretry_for=(RequestException, JSONDecodeError),
    default_retry_delay=600,
)
def parse_provider(provider_name):
    provider = BaseTapListProvider.get_provider(provider_name)()
    LOG.debug('Got provider: %s', provider.__class__.__name__)
    venues = provider.get_venues(ids_only=True)
    LOG.debug('Got venue IDs: %s', venues)
    for venue in venues:
        parse_venue.delay(venue['id'], provider_name)
    LOG.debug('Done')


@shared_task(
    bind=True,
    autoretry_for=(RequestException, JSONDecodeError, IntegrityError),
    default_retry_delay=600,
)
def parse_venue(self, venue_id, provider_name):
    provider = BaseTapListProvider.get_provider(provider_name)()
    venue = Venue.objects.select_related(
        'api_configuration',
    ).filter(
        tap_list_provider=provider_name,
        api_configuration__isnull=False,
    ).prefetch_related(
        Prefetch(
            'taps',
            queryset=Tap.objects.select_related('beer__manufacturer'),
        ),
    ).get(id=venue_id)
    LOG.info('Parsing venue %s (provider %s)', venue.name, provider_name)
    try:
        with transaction.atomic():
            provider.handle_venue(venue)
    except OperationalError as exc:
        if 'deadlock detected' in str(exc):
            # we hit a deadlock creating a manufacturer or style
            raise self.retry(countdown=5, exc=exc)
        raise
