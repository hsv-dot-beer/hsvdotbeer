import json
from django.urls import reverse
from django.forms.models import model_to_dict
from nose.tools import eq_
from rest_framework.test import APITestCase
from rest_framework import status
from faker import Faker

from hsv_dot_beer.users.test.factories import UserFactory
from events.models import Event
from .factories import EventFactory

fake = Faker()


class TestEventListTestCase(APITestCase):
    """
    Tests /venues list operations.
    """

    def setUp(self):
        self.url = reverse('event-list')
        # use .build() so we don't needlessly save the event
        self.event = EventFactory.build()
        # have to save the related field to get a PK
        self.event.venue.save()
        # now buid our POST payload
        self.event_data = model_to_dict(self.event)
        for field in ['start_time', 'end_time']:
            self.event_data[field] = self.event_data[field].isoformat()
        self.event_data['venue_id'] = self.event.venue.id
        del self.event_data['venue']
        # last, create the user
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
            self.url, json.dumps(self.event_data),
            content_type='application/json')
        eq_(response.status_code, status.HTTP_201_CREATED, response.data)

        event = Event.objects.get(pk=response.data.get('id'))
        eq_(event.title, self.event_data.get('title'))
        eq_(event.description, self.event_data.get('description'))


class TestEventDetailTestCase(APITestCase):
    """
    Tests /venues detail operations.
    """

    def setUp(self):
        self.event = EventFactory()
        self.url = reverse('event-detail', kwargs={'pk': self.event.pk})
        self.user = UserFactory(is_staff=True)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Token {self.user.auth_token}')

    def test_get_request_returns_a_given_venue(self):
        response = self.client.get(self.url)
        eq_(response.status_code, status.HTTP_200_OK)

    def test_patch_request_updates_a_venue(self):
        new_name = fake.first_name()
        payload = {'title': new_name}
        response = self.client.patch(self.url, payload)
        eq_(response.status_code, status.HTTP_200_OK, response.data)

        event = Event.objects.get(pk=self.event.id)
        eq_(event.title, new_name)
