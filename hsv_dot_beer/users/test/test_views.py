import json

from django.urls import reverse
from django.forms.models import model_to_dict
from django.contrib.auth.hashers import check_password
from nose.tools import ok_, eq_
from rest_framework.test import APITestCase
from rest_framework import status
from faker import Faker

from beers.test.factories import BeerFactory
from beers.models import UserFavoriteBeer
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

    def test_post_request_with_no_data_fails(self):
        user = UserFactory(is_staff=True)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {user.auth_token}")
        response = self.client.post(self.url, {})
        eq_(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_request_with_valid_data_succeeds(self):
        user = UserFactory(is_staff=True)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {user.auth_token}")
        response = self.client.post(
            self.url,
            json.dumps(self.user_data),
            content_type="application/json",
        )
        eq_(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(pk=response.data.get("id"))
        eq_(user.username, self.user_data.get("username"))
        ok_(check_password(self.user_data.get("password"), user.password))

    def test_post_request_unauthorized(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.post(
            self.url,
            json.dumps(self.user_data),
            content_type="application/json",
        )
        eq_(response.status_code, status.HTTP_403_FORBIDDEN)


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
        eq_(response.status_code, status.HTTP_200_OK)

    def test_put_request_updates_a_user(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.user.auth_token}",
        )

        new_first_name = fake.first_name()
        payload = {"first_name": new_first_name}
        response = self.client.put(self.url, payload)
        eq_(response.status_code, status.HTTP_200_OK)

        user = User.objects.get(pk=self.user.id)
        eq_(user.first_name, new_first_name)

    def test_subscribe_to_beer(self):
        beer = BeerFactory()
        url = reverse("user-subscribetobeer", kwargs={"pk": self.user.pk})
        print(url)
        payload = {
            "beer": beer.id,
            "notifications_enabled": True,
        }
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.user.auth_token}",
        )

        response = self.client.post(url, payload)
        eq_(response.status_code, status.HTTP_200_OK, response.data)
        eq_(UserFavoriteBeer.objects.count(), 1)

    def test_update_subscription_to_beer(self):
        beer = BeerFactory()
        sub = UserFavoriteBeer.objects.create(
            beer=beer,
            user=self.user,
            notifications_enabled=True,
        )
        url = reverse("user-subscribetobeer", kwargs={"pk": self.user.pk})

        payload = {
            "beer": beer.id,
            "notifications_enabled": False,
        }
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.user.auth_token}",
        )

        response = self.client.post(url, payload)
        eq_(response.status_code, status.HTTP_200_OK, response.content)
        eq_(UserFavoriteBeer.objects.count(), 1)
        sub.refresh_from_db()
        self.assertFalse(sub.notifications_enabled)

    def test_unsubscribe_from_beer(self):
        beer = BeerFactory()
        UserFavoriteBeer.objects.create(
            beer=beer,
            user=self.user,
            notifications_enabled=True,
        )
        url = reverse("user-unsubscribefrombeer", kwargs={"pk": self.user.pk})

        payload = {
            "beer": beer.id,
            "notifications_enabled": False,
        }
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.user.auth_token}",
        )

        response = self.client.post(url, payload)
        eq_(response.status_code, status.HTTP_204_NO_CONTENT, response.content)
        eq_(UserFavoriteBeer.objects.count(), 0)
