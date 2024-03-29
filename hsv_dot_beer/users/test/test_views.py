import json

from django.urls import reverse
from django.forms.models import model_to_dict
from django.contrib.auth.hashers import check_password
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.response import Response
from faker import Faker
from ..models import User
from .factories import UserFactory

fake = Faker()


class TestUserListTestCase(APITestCase):
    """
    Tests /users list operations.
    """

    def setUp(self):
        self.url = reverse("user-list")
        self.user_data = model_to_dict(UserFactory.build())
        self.user_data["date_joined"] = self.user_data["date_joined"].isoformat()
        super().setUp()

    def test_post_request_with_no_data_fails(self):
        user = UserFactory(is_staff=True)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {user.auth_token}")
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_request_with_valid_data_succeeds(self):
        user = UserFactory(is_staff=True)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {user.auth_token}")
        response: Response = self.client.post(
            self.url,
            json.dumps(self.user_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(pk=response.data.get("id"))
        self.assertEqual(user.username, self.user_data.get("username"))
        self.assertTrue(check_password(self.user_data.get("password"), user.password))

    def test_post_request_unauthorized(self):
        response = self.client.post(
            self.url,
            json.dumps(self.user_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestUserDetailTestCase(APITestCase):
    """
    Tests /users detail operations.
    """

    def setUp(self):
        self.user = UserFactory()
        self.url = reverse("user-detail", kwargs={"pk": self.user.pk})
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.user.auth_token}")

    def test_get_request_returns_a_given_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_request_updates_a_user(self):
        new_first_name = fake.first_name()
        payload = {"first_name": new_first_name}
        response = self.client.put(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user = User.objects.get(pk=self.user.id)
        self.assertEqual(user.first_name, new_first_name)
