from django.urls import reverse
from django.forms.models import model_to_dict
from nose.tools import eq_
from rest_framework.test import APITestCase
from rest_framework import status
from faker import Faker

from hsv_dot_beer.users.test.factories import UserFactory
from beers.models import BeerStyle, BeerStyleTag, BeerStyleCategory
from .factories import BeerStyleFactory, BeerStyleTagFactory

fake = Faker()


class TestBeerStyleListTestCase(APITestCase):
    def setUp(self):
        self.tags = [BeerStyleTagFactory.create(),
                     BeerStyleTagFactory.create()]
        self.style = BeerStyleFactory.create(tags=self.tags)

        self.url = reverse('beerstyle-detail', kwargs={'pk': self.style.pk})
        self.user = UserFactory()
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')


    def test_get_request_returns_a_style(self):
        response = self.client.get(self.url)
        eq_(response.status_code, status.HTTP_200_OK)

    def test_patch_doesnt_change_tags(self):
        new_name = fake.first_name()
        payload = {'name': new_name}

        response = self.client.patch(self.url, payload)
        eq_(response.status_code, status.HTTP_200_OK, response.data)

        style = BeerStyle.objects.get(pk=self.style.id)
        eq_(len(self.tags), style.tags.count())

    def test_patch_can_clear_tags(self):
        payload = {'name': 'asdfadsfasdfadsf', 'tags': []}

        response = self.client.patch(self.url, payload)
        eq_(response.status_code, status.HTTP_200_OK, response.data)

        style = BeerStyle.objects.get(pk=self.style.id)
        #TODO Enable this test?
        #eq_(0, style.tags.count())

    def test_patch_without_category_id(self):
        new_name = fake.first_name()
        payload = {'name': new_name}

        response = self.client.patch(self.url, payload)
        eq_(response.status_code, status.HTTP_200_OK, response.data)

        style = BeerStyle.objects.get(pk=self.style.id)
        eq_(self.style.category, style.category)
