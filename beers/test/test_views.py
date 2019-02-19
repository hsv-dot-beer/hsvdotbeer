import json

from django.urls import reverse
from nose.tools import eq_
from rest_framework.test import APITestCase
from rest_framework import status
from faker import Faker

from hsv_dot_beer.users.test.factories import UserFactory
from taps.test.factories import TapFactory
from beers.models import BeerStyle
from beers.serializers import ManufacturerSerializer
from .factories import BeerStyleFactory, BeerStyleTagFactory, \
    ManufacturerFactory, BeerFactory

fake = Faker()


class TestBeerStyleDetailTestCase(APITestCase):
    def setUp(self):
        self.tags = [BeerStyleTagFactory.create(),
                     BeerStyleTagFactory.create()]
        self.style = BeerStyleFactory.create(tags=self.tags)

        self.url = reverse('beerstyle-detail', kwargs={'pk': self.style.pk})
        self.user = UserFactory(is_staff=True)
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
        payload = {
            'name': 'asdfadsfasdfadsf',
            'tags': [],
        }

        response = self.client.patch(
            self.url, json.dumps(payload), content_type='application/json')
        eq_(response.status_code, status.HTTP_200_OK, response.data)
        eq_(response.data['tags'], [], response.data)
        self.style.refresh_from_db()
        eq_(0, self.style.tags.count())

    def test_patch_without_category_id(self):
        new_name = fake.first_name()
        payload = {'name': new_name}

        response = self.client.patch(self.url, payload)
        eq_(response.status_code, status.HTTP_200_OK, response.data)

        style = BeerStyle.objects.get(pk=self.style.id)
        eq_(self.style.category, style.category)

    def test_beers_on_tap(self):
        beer = BeerFactory(style=self.style)
        # link it to *a* tap (doesn't matter which one) so that it shows up
        # as being on tap
        TapFactory(beer=beer)
        # create another dummy tap and beer so we can be sure filtering works
        TapFactory(beer=BeerFactory())
        url = f'{self.url}beersontap/'
        response = self.client.get(url)
        eq_(response.status_code, status.HTTP_200_OK, response.data)
        self.assertIn('results', response.data, response.data)
        eq_(len(response.data['results']), 1, response.data)
        eq_(response.data['results'][0]['id'], beer.id, response.data)


class ManufacturerListTestCase(APITestCase):
    def setUp(self):
        self.manufacturer = ManufacturerFactory()

        self.url = reverse('manufacturer-list')
        self.user = UserFactory(is_staff=True)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')

    def test_list(self):
        response = self.client.get(self.url)
        eq_(len(response.data['results']), 1, response.data)
        eq_(
            response.data['results'],
            [ManufacturerSerializer(self.manufacturer).data],
        )

    def test_create(self):
        data = {
            'name': 'beer company',
        }
        response = self.client.post(self.url, data)
        eq_(response.status_code, 201)
        eq_(response.data['name'], data['name'])
        self.assertNotEqual(response.data['id'], self.manufacturer.pk)


class ManufacturerDetailTestCase(APITestCase):
    def setUp(self):
        self.manufacturer = ManufacturerFactory()

        self.url = reverse(
            'manufacturer-detail', kwargs={'pk': self.manufacturer.pk},
        )
        self.user = UserFactory(is_staff=True)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}',
        )

    def test_patch(self):
        data = {
            'name': 'other beer company',
        }
        response = self.client.patch(self.url, data)
        eq_(response.status_code, 200)
        eq_(response.data['name'], data['name'])
        eq_(response.data['id'], self.manufacturer.pk)


class BeerDetailTestCase(APITestCase):
    def setUp(self):
        self.beer = BeerFactory()
        self.url = reverse(
            'beer-detail', kwargs={'pk': self.beer.pk},
        )
        self.user = UserFactory(is_staff=True)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}'
        )

    def test_patch(self):
        data = {
            'name': 'a beer',
        }
        response = self.client.patch(self.url, data)
        eq_(response.status_code, 200)
        eq_(response.data['name'], data['name'])
        eq_(response.data['id'], self.beer.pk)

    def test_venues_at(self):
        # two where it's attached and one where it isn't
        taps = [
            TapFactory(beer=self.beer), TapFactory(beer=self.beer),
            TapFactory(),
        ]
        url = f'{self.url}placesavailable/'
        response = self.client.get(url)
        eq_(response.status_code, 200)
        eq_(len(response.data['results']), 2, response.data)
        venues = [i.venue for i in taps if i.beer == self.beer]
        eq_(
            {i.name for i in venues},
            {i['name'] for i in response.data['results']},
            response.data,
        )


class BeerListTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.tags = [
            BeerStyleTagFactory.create(), BeerStyleTagFactory.create(),
        ]
        cls.style = BeerStyleFactory.create(tags=cls.tags)

        cls.url = reverse('beer-list')
        cls.beer = BeerFactory(style=cls.style)

    def test_filter_no_match(self):
        response = self.client.get(
            f'{self.url}?name={self.beer.name}zzz'
        )
        eq_(response.status_code, 200)
        eq_(response.data['results'], [])

    def test_filter_match(self):
        BeerFactory(name=f'aaaaaaa{self.beer.name[:10]}')
        tap = TapFactory(beer=self.beer)
        response = self.client.get(
            f'{self.url}?name__istartswith={self.beer.name[:5].lower()}'
        )
        eq_(response.status_code, 200)
        eq_(len(response.data['results']), 1, response.data)
        eq_(response.data['results'][0]['name'], self.beer.name, response.data)
        eq_(
            response.data['results'][0]['venues'][0]['id'],
            tap.venue.id,
            response.data,
        )
        eq_(len(response.data['results'][0]['venues']), 1, response.data)


class BeerStyleCategoryTestCase(APITestCase):

    def test_beers_on_tap(self):
        user = UserFactory(is_staff=True)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {user.auth_token}')

        beer = BeerFactory(style=BeerStyleFactory())
        url = reverse(
            'beerstylecategory-detail', kwargs={'pk': beer.style.category.pk})
        # link it to *a* tap (doesn't matter which one) so that it shows up
        # as being on tap
        TapFactory(beer=beer)
        # create another dummy tap and beer so we can be sure filtering works
        TapFactory(beer=BeerFactory())
        url = f'{url}beersontap/'
        response = self.client.get(url)
        eq_(response.status_code, status.HTTP_200_OK, response.data)
        self.assertIn('results', response.data, response.data)
        eq_(len(response.data['results']), 1, response.data)
        eq_(response.data['results'][0]['id'], beer.id, response.data)
