"""
Test tweeting about beer.

Doesn't test the most important rule: never tweet.
"""

from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from celery import Task

from beers.test.factories import BeerFactory
from taps.test.factories import TapFactory
from venues.test.factories import VenueFactory
from tap_list_providers.tasks import (
    tweet_about_beers, SINGLE_BEER_TEMPLATE, MULTI_BEER_INNER, MULTI_BEER_OUTER,
)


class TweetTestCase(TestCase):

    def setUp(self):
        self.venue = VenueFactory()
        self.api_key = '12345'
        self.api_secret = '23456'
        self.consumer_key = '32sdfasd'
        self.consumer_secret = 'sgbbdabd'

    def settings_context_manager(self):
        return self.settings(
            TWITTER_CONSUMER_KEY=self.consumer_key,
            TWITTER_CONSUMER_SECRET=self.consumer_secret,
            TWITTER_ACCESS_TOKEN_KEY=self.api_key,
            TWITTER_ACCESS_TOKEN_SECRET=self.api_secret,
        )

    @patch('tap_list_providers.tasks.Api')
    @patch.object(Task, 'retry')
    def test_single_beer(self, mock_retry, mock_api):
        beer = BeerFactory()
        TapFactory(venue=self.venue, beer=beer)
        with self.settings_context_manager():
            tweet_about_beers([beer.id])
        mock_retry.assert_not_called()
        mock_api.assert_called_once_with(
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            access_token_key=self.api_key,
            access_token_secret=self.api_secret,
        )
        mock_api.return_value.PostUpdate.assert_called_once_with(
            SINGLE_BEER_TEMPLATE.format(
                beer.name,
                '@' + beer.manufacturer.twitter_handle,
                beer.style.name,
                self.venue.name,
            )
        )
        mock_api.return_value.PostUpdates.assert_not_called()

    @patch('tap_list_providers.tasks.Api')
    @patch.object(Task, 'retry')
    def test_single_beer_no_twitter(self, mock_retry, mock_api):
        beer = BeerFactory()
        beer.manufacturer.twitter_handle = ''
        beer.manufacturer.save()
        TapFactory(venue=self.venue, beer=beer)
        with self.settings_context_manager():
            tweet_about_beers([beer.id])
        mock_retry.assert_not_called()
        mock_api.assert_called_once_with(
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            access_token_key=self.api_key,
            access_token_secret=self.api_secret,
        )
        mock_api.return_value.PostUpdate.assert_called_once_with(
            SINGLE_BEER_TEMPLATE.format(
                beer.name,
                beer.manufacturer.name,
                beer.style.name,
                self.venue.name,
            )
        )
        mock_api.return_value.PostUpdates.assert_not_called()

    @patch('tap_list_providers.tasks.Api')
    @patch.object(Task, 'retry')
    def test_single_beer_venue_twitter(self, mock_retry, mock_api):
        beer = BeerFactory()
        self.venue.twitter_handle = 'gsdgsdgasvas'
        self.venue.save()
        TapFactory(venue=self.venue, beer=beer)
        with self.settings_context_manager():
            tweet_about_beers([beer.id])
        mock_retry.assert_not_called()
        mock_api.assert_called_once_with(
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            access_token_key=self.api_key,
            access_token_secret=self.api_secret,
        )
        mock_api.return_value.PostUpdate.assert_called_once_with(
            SINGLE_BEER_TEMPLATE.format(
                beer.name,
                '@' + beer.manufacturer.twitter_handle,
                beer.style.name,
                '@' + self.venue.twitter_handle,
            )
        )
        mock_api.return_value.PostUpdates.assert_not_called()
