from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from beers.test.factories import BeerFactory
from hsv_dot_beer.users.test.factories import UserFactory


class UnmappedStyleTestCase(APITestCase):

    def test_unmapped_list(self):
        beer = BeerFactory(api_vendor_style='my style')
        url = f"{reverse('TapListProviderStyleMapping-list'.lower())}unmapped/"
        user = UserFactory(is_staff=True)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {user.auth_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data), 1, response.data)
        self.assertEqual(
            response.data[0]['provider_style_name'],
            beer.api_vendor_style, response.data,
        )
