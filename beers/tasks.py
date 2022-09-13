"""Tasks for fetching untappd metadata"""
import os
import logging
import datetime
import random
from json import JSONDecodeError

from dateutil.parser import parse
import requests
from requests.exceptions import RequestException
from django.db.models import F
from django.utils.timezone import now
from django.db import transaction
from django.db.utils import IntegrityError
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError


from tap_list_providers.models import APIRateLimitTimestamp
from beers.models import (
    Beer,
    Manufacturer,
    UntappdMetadata,
    BeerPrice,
)


IS_LOCAL = os.environ.get("DJANGO_CONFIGURATION", "") == "Local"
LOG = logging.getLogger(__name__)


class UnexpectedResponseError(Exception):
    """Received an unexpected response from Untappd"""


@shared_task(
    bind=True,
    autoretry_for=(RequestException, UnexpectedResponseError, JSONDecodeError),
    default_retry_delay=600,
)
def look_up_beer(self, beer_pk):
    LOG.debug("Looking up Untappd data for %s", beer_pk)
    try:
        beer = (
            Beer.objects.filter(
                id=beer_pk,
            )
            .select_related("untappd_metadata")
            .get()
        )
    except Beer.DoesNotExist as exc:
        LOG.error("Beer ID %s not found!", beer_pk)
        raise self.retry(countdown=30, exc=exc)
    try:
        untappd_metadata = beer.untappd_metadata
    except UntappdMetadata.DoesNotExist:
        # not updated recently; don't care
        pass
    else:
        if now() - untappd_metadata.timestamp <= datetime.timedelta(minutes=360):
            LOG.debug("skipping recently updated data for %s", beer)
            return
    try:
        rate_limit_timestamp = APIRateLimitTimestamp.objects.get(api_type="untappd")
    except APIRateLimitTimestamp.DoesNotExist:
        rate_limit_timestamp = None
    else:
        if rate_limit_timestamp.rate_limit_expires_at >= now():
            LOG.info(
                "Currently rate-limited! Rate limit expires at %s",
                rate_limit_timestamp.rate_limit_expires_at,
            )
            jitter = random.SystemRandom().randint(0, 30)
            countdown = rate_limit_timestamp.rate_limit_expires_at - now()
            raise self.retry(countdown=countdown.seconds + jitter)
        rate_limit_timestamp.delete()
    LOG.debug("Looking up Untappd data for %s", beer)
    if not beer.untappd_url:
        LOG.error("Beer %s (PK %s) not linked to Untappd", beer, beer_pk)
        return False
    untappd_args = {}
    try:
        untappd_args["client_id"] = os.environ["UNTAPPD_CLIENT_ID"]
        untappd_args["client_secret"] = os.environ["UNTAPPD_CLIENT_SECRET"]
    except KeyError as exc:
        try:
            untappd_args["access_token"] = os.environ["UNTAPPD_ACCESS_TOKEN"]
        except KeyError:
            if IS_LOCAL:
                LOG.warning("Untappd API credentials not specified. Quitting.")
                return
            raise ValueError(
                "You must specify environment variables for Untappd API Access!"
            ) from exc
    untappd_pk = beer.untappd_url.rsplit("/", 1)[-1]
    untappd_url = f"https://api.untappd.com/v4/beer/info/{untappd_pk}"
    result = requests.get(untappd_url, params=untappd_args)
    if result.status_code == 429:
        try:
            expires = parse(result.headers["X-Ratelimit-Expired"])
        except KeyError:
            LOG.error(
                "Got 429 from Untappd without expiration! headers %s",
                result.headers,
            )
            return None
        LOG.warning("Hit Untappd API rate limit! Limit opens up at %s", expires)
        # retry in 1 hour
        if rate_limit_timestamp:
            rate_limit_timestamp.rate_limit_expires_at = expires
            rate_limit_timestamp.save()
        else:
            # do an update or create to attempt to minimize transaction
            # issues
            try:
                with transaction.atomic():
                    APIRateLimitTimestamp.objects.update_or_create(
                        api_type="untappd", defaults={"rate_limit_expires_at": expires}
                    )
            except IntegrityError:
                # well that didn't work. This must happen if we've got another
                # rate limit situation going on, so assume that one passed
                pass
        jitter = random.SystemRandom().randint(0, 30)
        countdown = expires - now()
        try:
            raise self.retry(countdown=countdown.seconds + jitter)
        except MaxRetriesExceededError:
            LOG.warning("Ran out of retries. We must be hurting.")
            return None

    # retry sooner for all other status codes
    result.raise_for_status()
    json_body = result.json()
    beer_data = {}
    try:
        if json_body["meta"]["code"] != 200:
            raise UnexpectedResponseError(
                f"Received unexpected body from Untappd: {json_body}",
            )
        beer_data = json_body["response"]["beer"]
    except KeyError as exc:
        raise UnexpectedResponseError(
            f"Received unexpected body from Untappd: {json_body}",
        ) from exc
    for key in ["checkins", "media"]:
        # scrap some big objects
        try:
            del beer_data[key]
        except KeyError:
            # don't care
            pass
    LOG.debug("Got Untappd data for %s: %s", beer, beer_data)
    UntappdMetadata.objects.update_or_create(
        beer=beer,
        defaults={
            "json_data": beer_data,
        },
    )
    if beer_data.get("beer_label_hd") and beer.logo_url != beer_data["beer_label_hd"]:
        LOG.info("Saving HD logo for %s", beer)
        beer.logo_url = beer_data["beer_label_hd"]
        beer.save()


@shared_task
def prune_stale_data():
    threshold = now() - datetime.timedelta(days=1)
    result = UntappdMetadata.objects.filter(timestamp__lt=threshold).delete()
    LOG.info("Cleaned up old untappd data: %s", result)


@shared_task
def purge_unused_prices():
    queryset = BeerPrice.objects.filter(
        beer__taps__isnull=True,
    )
    LOG.info("Purging %s prices of unused beers", queryset.distinct().count())
    queryset.delete()
    LOG.info("Done. %s prices remain", BeerPrice.objects.count())


@shared_task
def purge_duplicate_alt_names():
    beer_names_deleted = 0
    for beer in Beer.objects.filter(alternate_names__contains=[F("name")]):
        beer.alternate_names.remove(beer.name)
        beer.save()
        beer_names_deleted += 1
    mfg_names_deleted = 0
    for mfg in Manufacturer.objects.filter(alternate_names__contains=[F("name")]):
        mfg.alternate_names.remove(mfg.name)
        mfg.save()
        mfg_names_deleted += 1
    LOG.info(
        "Beer alt names deleted: %s, Mfg alt names %s",
        beer_names_deleted,
        mfg_names_deleted,
    )
