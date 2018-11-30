from django.urls import reverse
from django.forms.models import model_to_dict
from nose.tools import eq_
from rest_framework.test import APITestCase
from rest_framework import status
from faker import Faker

from hsv_dot_beer.users.test.factories import UserFactory
from venues.models import Venue, VenueAPIConfiguration, Room
from .factories import VenueFactory

fake = Faker()


class TestVenueListTestCase(APITestCase):
    """
    Tests /venues list operations.
    """

    def setUp(self):
        self.url = reverse('venue-list')
        self.venue_data = model_to_dict(VenueFactory.build())
        self.user = UserFactory()
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')

    def test_post_request_with_no_data_fails(self):
        response = self.client.post(self.url, {})
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_post_request_with_valid_data_succeeds(self):
        response = self.client.post(self.url, self.venue_data)
        eq_(response.status_code, status.HTTP_201_CREATED, response.data)

        venue = Venue.objects.get(pk=response.data.get('id'))
        eq_(venue.name, self.venue_data.get('name'))
        eq_(venue.time_zone.zone, self.venue_data.get('time_zone'))


class TestVenueDetailTestCase(APITestCase):
    """
    Tests /venues detail operations.
    """

    def setUp(self):
        self.venue = VenueFactory()
        self.url = reverse('venue-detail', kwargs={'pk': self.venue.pk})
        self.user = UserFactory()
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')

    def test_get_request_returns_a_given_venue(self):
        response = self.client.get(self.url)
        eq_(response.status_code, status.HTTP_200_OK)

    def test_put_request_updates_a_venue(self):
        new_name = fake.first_name()
        payload = {'name': new_name}
        response = self.client.put(self.url, payload)
        eq_(response.status_code, status.HTTP_200_OK, response.data)

        venue = Venue.objects.get(pk=self.venue.id)
        eq_(venue.name, new_name)


class VenueAPIConfigurationListTestCase(APITestCase):

    def setUp(self):
        self.venue = VenueFactory()
        self.admin_user = UserFactory(is_staff=True)
        self.url = reverse('venueapiconfiguration-list')
        print(self.url)
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


class RoomListTestCase(APITestCase):
    """
    Tests /venues/rooms list operations.
    """

    def setUp(self):
        self.url = reverse('room-list')
        self.venue = VenueFactory()
        self.user = UserFactory()
        self.room_data = {
            'venue_id': self.venue.id,
            'name': 'test room',
            'description': 'no',
        }
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')

    def test_post_request_with_no_data_fails(self):
        response = self.client.post(self.url, {})
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_post_request_with_valid_data_succeeds(self):
        response = self.client.post(self.url, self.room_data)
        eq_(response.status_code, status.HTTP_201_CREATED, response.data)

        room = Room.objects.get(pk=response.data.get('id'))
        eq_(room.name, self.room_data.get('name'))
        eq_(room.venue_id, self.venue.id)
        eq_(room.description, self.room_data['description'])


class RoomDetailTestCase(APITestCase):
    """
    Tests /venues/rooms detail operations.
    """

    def setUp(self):
        self.venue = VenueFactory()
        self.room = Room.objects.create(venue=self.venue, name='foo')
        self.url = reverse('room-detail', kwargs={'pk': self.room.pk})
        self.user = UserFactory()
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

        room = Room.objects.get(pk=self.room.id)
        eq_(room.name, new_name)
