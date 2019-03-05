#!/usr/bin/env python
"""Tasks for tap list providers"""

import logging

from celery import shared_task


from tap_list_providers.base import BaseTapListProvider
# this import is needed for the subclass lookup to work
from tap_list_providers.parsers import (  # noqa
    digitalpour, thenook, taphunter, untappd, stemandstein,
)


LOG = logging.getLogger(__name__)


@shared_task
def parse_provider(provider_name):
    provider = BaseTapListProvider.get_provider(provider_name)()
    LOG.debug('Got provider: %s', provider.__class__.__name__)
    venues = provider.get_venues()
    LOG.debug('Got venues: %s', [str(i) for i in venues])
    provider.handle_venues(venues)
    LOG.debug('Done')
