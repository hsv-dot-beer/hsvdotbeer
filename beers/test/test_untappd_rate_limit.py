from unittest.mock import patch
import datetime
import json

from django.test import TestCase
import responses
from celery import Task
from celery.exceptions import Retry
from freezegun import freeze_time

from tap_list_providers.models import APIRateLimitTimestamp
from beers.models import UntappdMetadata
from beers.tasks import look_up_beer
from beers.test.factories import BeerFactory


class TestUntappdRateLimit(TestCase):
    def setUp(self):
        self.beer = BeerFactory(
            untappd_url="https://untappd.com/b/omnipollo-hypnopompa/432069"
        )
        self.untappd_url = "https://api.untappd.com/v4/beer/info/432069"
        # just enough to avoid exceptions
        self.json_data = json.dumps(
            {
                "response": {"beer": {}},
                "meta": {"code": 200},
            }
        )
        self.limit_headers = {
            "Date": "Fri, 15 Nov 2019 02:24:36 GMT",
            "Content-Type": "application/json; charset=UTF-8",
            "Transfer-Encoding": "chunked",
            "Connection": "keep-alive",
            "Server": "nginx",
            "X-Ratelimit-Expired": "Fri, 15 Nov 2019 03:00:00 +0000",
            "X-Ratelimit-Limit": "100",
            "X-Ratelimit-Remaining": "0",
            "X-Auth-Type": "key",
            "X-API-Version": "4",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT",
            "Access-Control-Allow-Headers": "Origin,Content-Type,Accept,"
            "X-Untappd-App,X-Untappd-App-Version",
        }

    @responses.activate
    @patch.object(Task, "retry")
    def test_no_retry(self, mock_retry):
        mock_retry.side_effect = Retry()
        responses.add(
            responses.GET,
            self.untappd_url,
            body=self.json_data,
            status=200,
        )
        self.assertFalse(UntappdMetadata.objects.exists())
        look_up_beer(self.beer.id)
        self.assertTrue(UntappdMetadata.objects.filter(beer=self.beer).exists())
        mock_retry.assert_not_called()

    @freeze_time("2019-11-15 02:30:00")
    @responses.activate
    def test_retry_no_existing_data(self):
        responses.add(
            responses.GET,
            self.untappd_url,
            status=429,
            headers=self.limit_headers,
        )
        self.assertFalse(UntappdMetadata.objects.exists())
        with self.assertRaises(Retry):
            look_up_beer(self.beer.id)
        self.assertFalse(UntappdMetadata.objects.filter(beer=self.beer).exists())
        untappd_timestamp = APIRateLimitTimestamp.objects.get()
        self.assertEqual(
            untappd_timestamp.rate_limit_expires_at,
            datetime.datetime(2019, 11, 15, 3, 0, 0, tzinfo=datetime.timezone.utc),
        )

    @freeze_time("2019-11-15 02:30:00")
    @responses.activate
    def test_retry_lockout_active(self):
        APIRateLimitTimestamp.objects.create(
            api_type="untappd",
            rate_limit_expires_at=datetime.datetime(
                2019,
                11,
                15,
                3,
                0,
                0,
                tzinfo=datetime.timezone.utc,
            ),
        )
        responses.add(
            responses.GET,
            self.untappd_url,
            status=200,
            # will trigger an exception if this gets called
            body="{}",
        )
        self.assertFalse(UntappdMetadata.objects.exists())
        with self.assertRaises(Retry):
            look_up_beer(self.beer.id)
        self.assertFalse(UntappdMetadata.objects.filter(beer=self.beer).exists())
        untappd_timestamp = APIRateLimitTimestamp.objects.get()
        self.assertEqual(
            untappd_timestamp.rate_limit_expires_at,
            datetime.datetime(
                2019,
                11,
                15,
                3,
                0,
                0,
                tzinfo=datetime.timezone.utc,
            ),
        )

    @freeze_time("2019-11-15 03:00:01")
    @responses.activate
    def test_retry_lockout_expired(self):
        APIRateLimitTimestamp.objects.create(
            api_type="untappd",
            rate_limit_expires_at=datetime.datetime(
                2019,
                11,
                15,
                3,
                0,
                0,
                tzinfo=datetime.timezone.utc,
            ),
        )
        responses.add(
            responses.GET,
            self.untappd_url,
            status=200,
            body=self.json_data,
        )
        self.assertFalse(UntappdMetadata.objects.exists())
        look_up_beer(self.beer.id)
        self.assertTrue(UntappdMetadata.objects.filter(beer=self.beer).exists())
        self.assertFalse(APIRateLimitTimestamp.objects.exists())
