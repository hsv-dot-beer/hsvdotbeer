#!/usr/bin/env python
"""Tasks for tap list providers"""

from json import JSONDecodeError
import logging

from django.conf import settings
from requests.exceptions import RequestException
from celery import shared_task
from twitter.api import Api, CHARACTER_LIMIT
from twitter.error import TwitterError
from twitter.twitter_utils import calc_expected_status_length


from tap_list_providers.base import BaseTapListProvider
# this import is needed for the subclass lookup to work
from tap_list_providers.parsers import (  # noqa
    digitalpour, taphunter, untappd, stemandstein, taplist_io,
)

RETRYABLE_ERRORS = {
    "Capacity Error",
    "Technical Error",
    "Exceeded connection limit for user",
}


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


def get_twitter_rate_limit_delay(api, endpoint='statuses/update'):
    """Calculate the number of seconds to wait before retrying"""
    rate_limit = api.rate_limit.get_limit(endpoint)
    timestamp = now().timestamp
    if not rate_limit:
        return None
    return rate_limit.reset - timestamp


@shared_task(bind=True)
def test_tweet(self):
    consumer_key = settings.TWITTER_CONSUMER_KEY
    consumer_secret = settings.TWITTER_CONSUMER_SECRET
    access_key = settings.TWITTER_ACCESS_TOKEN_KEY
    access_secret = settings.TWITTER_ACCESS_TOKEN_SECRET
    if any(
        not i for i in [
            consumer_key, consumer_secret, access_key, access_secret,
        ]
    ):
        LOG.warning('Twitter API credentials not set!')
        return
    api = Api(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token_key=access_key,
        access_token_secret=access_secret,
    )
    message = 'Hello World! I know nothing.'
    try:
        if calc_expected_status_length(message) > CHARACTER_LIMIT:
            api.PostUpdates(message, continuation='…')
        else:
            api.PostUpdate(message)
    except TwitterError as exc:
        LOG.warning('Hit twitter error: %s', exc)
        if str(exc) in RETRYABLE_ERRORS:
            raise self.retry(exc=exc)
        delay = get_twitter_rate_limit_delay(api)
        if delay is None:
            LOG.error('No idea what to do with twitter error %s', exc)
            raise
        raise self.retry(countdown=delay, exc=exc)
