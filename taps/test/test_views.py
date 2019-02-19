from django.urls import reverse
from nose.tools import eq_
from rest_framework.test import APITestCase
from rest_framework import status
from faker import Faker

from hsv_dot_beer.users.test.factories import UserFactory
from venues.test.factories import VenueFactory
from .factories import TapFactory

fake = Faker()


class TestTapDetailTestCase(APITestCase):
    def setUp(self):
        self.venue = VenueFactory()
        self.tap = TapFactory(venue=self.venue)

        self.url = reverse('tap-detail', kwargs={'pk': self.tap.pk})
        self.user = UserFactory(is_staff=True)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')

    def test_get_request_returns_a_tap(self):
        response = self.client.get(self.url)
        eq_(response.status_code, status.HTTP_200_OK)

    def test_patch_rejects_default(self):
        other = TapFactory(venue=self.venue)
        payload = {'tap_number': other.tap_number}

        response = self.client.patch(self.url, payload)
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
