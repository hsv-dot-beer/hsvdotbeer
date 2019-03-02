"""Tasks for fetching untappd metadata"""
import os
import logging
import datetime
from json import JSONDecodeError

import requests
from requests.exceptions import RequestsException
from django.utils.timezone import now
from celery import shared_task


from beers.models import Beer, UntappdMetadata


LOG = logging.getLogger(__name__)


class UnexpectedResponseError(Exception):
    """Received an unexpected response from Untappd"""


@shared_task(
    autoretry_for=(RequestsException, JSONDecodeError),
    retry_backoff=True,
)
def look_up_beer(beer_pk):
    LOG.debug('Looking up Untappd data for %s', beer_pk)
    try:
        beer = Beer.objects.filter(
            id=beer_pk,
        ).select_related('untappd_metadata').get()
    except Beer.DoesNotExist:
        LOG.error('Beer ID %s not found!', beer_pk)
        return False
    try:
        untappd_metadata = beer.untappd_metadata
    except UntappdMetadata.DoesNotExist:
        # not updated recently; don't care
        pass
    else:
        if now() - untappd_metadata.timestamp <= datetime.timedelta(minutes=30):
            LOG.debug('skipping recently updated data for %s', beer)
            return
    LOG.debug('Looking up Untappd data for %s', beer)
    if not beer.untappd_url:
        LOG.error('Beer %s (PK %s) not linked to Untappd', beer, beer_pk)
        return False
    untappd_args = {}
    try:
        untappd_args['client_id'] = os.environ['UNTAPPD_CLIENT_ID']
        untappd_args['client_secret'] = os.environ['UNTAPPD_CLIENT_SECRET']
    except KeyError:
        try:
            untappd_args['access_token'] = os.environ['UNTAPPD_ACCESS_TOKEN']
        except KeyError:
            raise ValueError(
                'You must specify environment variables for Untappd API Access!'
            )
    untappd_pk = beer.untappd_url.rsplit('/', 1)[-1]
    untappd_url = f'https://api.untappd.com/v4/beer/info/{untappd_pk}'
    result = requests.get(untappd_url, params=untappd_args)
    result.raise_for_status()
    UntappdMetadata.objects.update_or_create(
        beer=beer,
        defaults={
            'json_data': result.json(),
        },
    )


@shared_task
def prune_stale_data():
    threshold = now() - datetime.timedelta(days=1)
    result = UntappdMetadata.objects.filter(
        timestamp__lt=threshold
    ).delete()
    LOG.info('Cleaned up old untappd data: %s', result)
