from django.urls import reverse
from nose.tools import eq_
from rest_framework.test import APITestCase
from faker import Faker

from hsv_dot_beer.users.test.factories import UserFactory
from taps.test.factories import TapFactory
from beers.serializers import ManufacturerSerializer
from .factories import ManufacturerFactory, BeerFactory

fake = Faker()


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
        cls.url = reverse('beer-list')
        cls.beer = BeerFactory()

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

    def test_compound_match(self):
        """Test that searching for part of the beer name and mfg name works"""
        query_string = f'{self.beer.name[:10]}+{self.beer.manufacturer.name[:5]}'
        tap = TapFactory(beer=self.beer)
        response = self.client.get(
            f'{self.url}?search={query_string.upper()}',
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

    def test_on_tap_no_dupes(self):
        # create two taps for the beer
        TapFactory(beer=self.beer)
        TapFactory(beer=self.beer)
        # create another beer that isn't on tap
        BeerFactory()
        response = self.client.get(f'{self.url}?on_tap=True')
        eq_(response.status_code, 200)
        eq_(len(response.data['results']), 1, response.data)
        eq_(response.data['results'][0]['name'], self.beer.name, response.data)
