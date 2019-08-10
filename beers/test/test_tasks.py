import os
from unittest.mock import patch

from celery import Task
from celery.exceptions import MaxRetriesExceededError
from django.test import TestCase
import responses

from ..tasks import look_up_beer
from .factories import BeerFactory


class TaskRetryTestCase(TestCase):
    """Validate that we don't get an exception when running out of retries"""

    def setUp(self):
        self.fake_url = 'https://untappd.com/beer/1'
        self.api_url = 'https://api.untappd.com/v4/beer/info/1'
        self.beer = BeerFactory(untappd_url=self.fake_url)

    @responses.activate
    @patch.object(Task, 'retry')
    def test_no_exception_on_retry(self, mock_retry):
        os.environ['UNTAPPD_CLIENT_ID'] = '1'
        os.environ['UNTAPPD_CLIENT_SECRET'] = '3'
        mock_retry.side_effect = MaxRetriesExceededError
        headers = {
            'Date': 'Wed, 07 Aug 2019 22:00:16 GMT',
            'Content-Type': 'application/json; charset=UTF-8',
            'Transfer-Encoding': 'chunked',
            'Connection': 'keep-alive',
            'Server': 'nginx',
            'X-Ratelimit-Expired': 'Wed, 07 Aug 2019 23:00:00 +0000',
            'X-Ratelimit-Limit': '100',
            'X-Ratelimit-Remaining': '0',
            'X-Auth-Type': 'key',
            'X-API-Version': '4',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, PUT',
            'Access-Control-Allow-Headers': 'Origin,Content-Type,Accept,'
            'X-Untappd-App,X-Untappd-App-Version',
        }
        responses.add(
            responses.GET,
            self.api_url,
            json={},
            status=429,
            headers=headers,
        )
        # if no exception, we're good
        result = look_up_beer(self.beer.id)
        self.assertIsNone(result)
        mock_retry.assert_called_once()
