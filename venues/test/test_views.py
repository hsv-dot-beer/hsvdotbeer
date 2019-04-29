import json
from django.urls import reverse
from django.forms.models import model_to_dict
from nose.tools import eq_
from rest_framework.test import APITestCase
from rest_framework import status
from faker import Faker

from hsv_dot_beer.users.test.factories import UserFactory
from venues.models import Venue, VenueAPIConfiguration
from beers.test.factories import BeerFactory
from taps.test.factories import TapFactory
from .factories import VenueFactory

fake = Faker()


class TestVenueListTestCase(APITestCase):
    """
    Tests /venues list operations.
    """

    def setUp(self):
        self.url = reverse('venue-list')
        self.venue_data = model_to_dict(VenueFactory.build())
        self.venue_data['country'] = str(self.venue_data['country'])
        self.user = UserFactory(is_staff=True)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')

    def test_post_request_with_no_data_fails(self):
        response = self.client.post(
            self.url, json.dumps({}), content_type='application/json',
        )
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_post_request_with_valid_data_succeeds(self):
        response = self.client.post(
            self.url, json.dumps(self.venue_data),
            content_type='application/json',
        )
        eq_(response.status_code, status.HTTP_201_CREATED, response.data)

        venue = Venue.objects.get(pk=response.data.get('id'))
        eq_(venue.name, self.venue_data.get('name'))
        eq_(venue.time_zone.zone, self.venue_data.get('time_zone'))

    def test_filtering(self):
        beer = BeerFactory()
        venue = VenueFactory()
        TapFactory(venue=venue, beer=beer)
        url = f'{self.url}?taps__beer__name__istartswith={beer.name.lower()[:5]}'
        response = self.client.get(url)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], venue.id, response.data)
        url = f'{self.url}?taps__beer__name={beer.name.lower()}aaaaa'
        response = self.client.get(url)
        self.assertEqual(len(response.data['results']), 0, response.data)


class TestVenueDetailTestCase(APITestCase):
    """
    Tests /venues detail operations.
    """

    def setUp(self):
        self.venue = VenueFactory()
        self.url = reverse('venue-detail', kwargs={'pk': self.venue.pk})
        self.user = UserFactory(is_staff=True)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')

    def test_get_request_returns_a_given_venue(self):
        response = self.client.get(self.url)
        eq_(response.status_code, status.HTTP_200_OK)

    def test_patch_request_updates_a_venue(self):
        new_name = fake.first_name()
        payload = {'name': new_name}
        response = self.client.patch(self.url, payload)
        eq_(response.status_code, status.HTTP_200_OK, response.data)

        venue = Venue.objects.get(pk=self.venue.id)
        eq_(venue.name, new_name)

    def test_beers(self):
        tap = TapFactory(venue=self.venue, beer=BeerFactory())
        BeerFactory()
        url = f'{self.url}beers/'
        response = self.client.get(url)
        eq_(response.status_code, status.HTTP_200_OK, response.data)
        eq_(len(response.data['results']), 1, response.data)
        eq_(response.data['results'][0]['id'], tap.beer_id)


class VenueAPIConfigurationListTestCase(APITestCase):

    def setUp(self):
        self.venue = VenueFactory()
        self.admin_user = UserFactory(is_staff=True)
        self.url = reverse('venueapiconfiguration-list')
        self.client.credentials = self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.admin_user.auth_token}')
        self.data = {
            'venue': self.venue.id,
            'url': 'https://example.com/',
        }

    def test_post_request_with_no_data_fails(self):
        response = self.client.post(self.url, {})
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_post_request_with_valid_data_succeeds(self):
        response = self.client.post(self.url, self.data)
        eq_(response.status_code, status.HTTP_201_CREATED, response.data)

        venue_config = VenueAPIConfiguration.objects.get(
            pk=response.data.get('id'))
        eq_(venue_config.venue_id, self.venue.id)
        eq_(venue_config.url, self.data['url'])


class VenueAPIConfigurationNormalUserTestCase(APITestCase):

    def setUp(self):
        self.venue = VenueFactory()
        self.admin_user = UserFactory(is_staff=False)
        self.url = reverse('venueapiconfiguration-list')
        self.client.credentials = self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.admin_user.auth_token}')
        self.data = {
            'venue': self.venue.id,
            'url': 'https://example.com/',
        }

    def test_normal_user(self):
        response = self.client.post(self.url, self.data)
        eq_(response.status_code, status.HTTP_403_FORBIDDEN, response.data)
