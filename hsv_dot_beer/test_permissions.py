from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from beers.test.factories import BeerFactory
from hsv_dot_beer.users.test.factories import UserFactory


class AuthTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.normal_user = UserFactory()
        cls.staff_user = UserFactory(is_staff=True)
        cls.beer = BeerFactory()
        cls.url = reverse('beer-detail', kwargs={'pk': cls.beer.id})

    def test_normal_user_get(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.normal_user.auth_token}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_normal_user_patch(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.normal_user.auth_token}')
        payload = {'name': 'foo'}

        response = self.client.patch(self.url, payload)
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_anon_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_anon_user_patch(self):
        payload = {'name': 'foo'}

        response = self.client.patch(self.url, payload)
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_staff_user_get(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.staff_user.auth_token}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_staff_user_patch(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.staff_user.auth_token}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        payload = {'name': 'foo'}

        response = self.client.patch(self.url, payload)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
