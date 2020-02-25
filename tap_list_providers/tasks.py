#!/usr/bin/env python
"""Tasks for tap list providers"""

from json import JSONDecodeError
import logging

from django.conf import settings
from django.db.models import Prefetch
from django.utils.timezone import now
from requests.exceptions import RequestException
from celery import shared_task
from twitter.api import CHARACTER_LIMIT
from twitter.error import TwitterError
from twitter.twitter_utils import calc_expected_status_length

from beers.models import Beer
from taps.models import Tap
from tap_list_providers.base import BaseTapListProvider
# this import is needed for the subclass lookup to work
from tap_list_providers.parsers import (  # noqa
    digitalpour, taphunter, untappd, stemandstein, taplist_io, beermenus,
)
from tap_list_providers.twitter_api import ThreadedApi

SINGLE_BEER_TEMPLATE = "We found a new beer! {} from {} (style: {}) on tap at {}"

MULTI_BEER_OUTER = """We found {} new beers! {}"""
MULTI_BEER_INNER = """- {} from {} (style: {}) on tap at {}"""

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
    new_beers = [
        i[0] for i in Beer.objects.filter(
            tweeted_about=False,
        ).values_list('id')
    ]
    if not new_beers:
        LOG.info('no new beers to tweet about')
        return
    LOG.debug('Scheduling tweet about new beers: %s', new_beers)
    # give ourselves a brief delay to give a quick chance at an untappd
    # lookup
    tweet_about_beers.s(new_beers).apply_async(countdown=300)
    LOG.debug('Done')


def format_venue(venue):
    """Format a venue for tweeting"""
    if venue.twitter_handle:
        if venue.twitter_short_location_description:
            return f'@{venue.twitter_handle} {venue.twitter_short_location_description}'
        return f'@{venue.twitter_handle}'
    return venue.name


def format_manufacturer(manufacturer):
    """Format a manufacturer for tweeting"""
    if manufacturer.twitter_handle:
        return f'@{manufacturer.twitter_handle}'
    return manufacturer.name


def format_venues(venues):
    if len(venues) == 1:
        venue_str = format_venue(venues[0])
    elif len(venues) == 2:
        venue_str = "{} and {}".format(
            format_venue(venues[0]),
            format_venue(venues[1]),
        )
    else:
        # yes, I'm doing this just for the oxford comma
        venue_str = "{}, and {}".format(
            ", ".join(format_venue(i) for i in venues[:-1]),
            format_venue(venues[-1]),
        )
    return venue_str


def format_beer(beer, beer_str):
    if beer.tweeted_about:
        LOG.info('Beer %s has already been announced on Twitter', beer)
        return
    taps = list(beer.taps.all())
    venues = list(sorted(
        set(i.venue for i in taps),
        # sort by display order
        key=lambda k: format_venue(k),
    ))
    venue_str = format_venues(venues)
    message = beer_str.format(
        beer.name,
        format_manufacturer(beer.manufacturer),
        beer.style.name if beer.style_id else 'unknown',
        venue_str,
    )
    return message


def format_beers(beers, format_str=MULTI_BEER_INNER):
    return [
        format_beer(beer, format_str)
        for beer in beers if not beer.tweeted_about
    ]


@shared_task(bind=True)
def tweet_about_beers(self, beer_pks):
    if not beer_pks:
        LOG.warning('nothing to do')
        return
    LOG.debug('Tweeting about beer PKs: %s', beer_pks)
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
    api = ThreadedApi(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token_key=access_key,
        access_token_secret=access_secret,
    )
    # Mark beers which have been removed from the tap list as tweeted about
    Beer.objects.filter(
        tweeted_about=False,
        taps__isnull=True,
    ).update(tweeted_about=True)
    beers = list(
        Beer.objects.filter(
            id__in=beer_pks,
            tweeted_about=False,
        ).select_related(
            'manufacturer', 'style',
        ).prefetch_related(
            Prefetch(
                'taps',
                queryset=Tap.objects.select_related('venue'),
            ),
        ).order_by('id')
    )
    already_tweeted_about = set(i.id for i in Beer.objects.filter(
        tweeted_about=True, id__in=beer_pks,
    ))
    unknown_pks = set(beer_pks).difference(already_tweeted_about)
    LOG.debug('Got %s beers', len(beers))
    if not beers:
        if unknown_pks:
            LOG.warning('No beers found! Trying again shortly')
            raise self.retry(countdown=300)
        LOG.info('everything was already tweeted about. No big deal')
        return
    if len(beers) > 10:
        LOG.info('Too many beers to tweet about at once: %s', len(beers))
        beers = beers[:10]
    if len(beers) == 1:
        beer = beers[0]
        if beer.tweeted_about:
            LOG.info('%s has already been tweeted about; skipping.', beer)
            return
        message = format_beer(beer, SINGLE_BEER_TEMPLATE).strip()
        messages = [message]
    else:
        extra_beers = len(beer_pks) - len(beers) - len(already_tweeted_about)
        messages = [
            MULTI_BEER_OUTER.format(
                len(beers),
                '({} still to come!)'.format(extra_beers)
                if extra_beers > 0 else ''
            ).strip()
        ] + format_beers(beers)
        if len(messages) == 1:
            LOG.info('All beers already tweeted about')
            return
    message = '\r\n'.join(messages)
    LOG.info('Going to tweet: %s', message)

    try:
        if calc_expected_status_length(message) > CHARACTER_LIMIT:
            api.PostUpdates(message, continuation='…', threaded=True)
        else:
            api.PostUpdate(message)
    except TwitterError as exc:
        LOG.warning('Hit twitter error: %s', exc)
        if str(exc) in RETRYABLE_ERRORS:
            raise self.retry(exc=exc)
        LOG.error('Tweet(s) that caused error was %s', message)
        delay = get_twitter_rate_limit_delay(api)
        if delay is None:
            LOG.error('No idea what to do with twitter error %s', exc)
            raise
        raise self.retry(countdown=delay, exc=exc)
    Beer.objects.filter(id__in=[i.id for i in beers]).update(tweeted_about=True)
    LOG.debug('Done tweeting')


def get_twitter_rate_limit_delay(api, endpoint='statuses/update'):
    """Calculate the number of seconds to wait before retrying"""
    rate_limit = api.rate_limit.get_limit(endpoint)
    timestamp = now().timestamp()
    if not rate_limit or not rate_limit.reset:
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
    api = ThreadedApi(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token_key=access_key,
        access_token_secret=access_secret,
    )
    message = 'This is a test long tweet\r\n{}'.format(
        '\r\n'.join(
            f'This is line {line}' for line in range(2, 30)
        )
    )
    try:
        if calc_expected_status_length(message) > CHARACTER_LIMIT:
            api.PostUpdates(message, continuation='…', threaded=True)
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
