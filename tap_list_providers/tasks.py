#!/usr/bin/env python
"""Tasks for tap list providers"""

from json import JSONDecodeError
import logging

from requests.exceptions import RequestException
from celery import shared_task


from tap_list_providers.base import BaseTapListProvider
# this import is needed for the subclass lookup to work
from tap_list_providers.parsers import (  # noqa
    digitalpour, thenook, taphunter, untappd, stemandstein, taplist_io,
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
    venues = provider.get_venues()
    LOG.debug('Got venues: %s', [str(i) for i in venues])
    provider.handle_venues(venues)
    LOG.debug('Done')
