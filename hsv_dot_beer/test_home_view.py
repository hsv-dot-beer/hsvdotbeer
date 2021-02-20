from django.test import TestCase
from django.urls import reverse

from hsv_dot_beer.users.test.factories import UserFactory
from venues.test.factories import VenueFactory
from venues.models import VenueTapManager


class TestHome(TestCase):
    def setUp(self):
        self.url = "/"
        # session, user, venues
        self.expected_queries = 3

    def test_superuser(self):
        user = UserFactory(is_superuser=True, is_staff=True)
        self.client.force_login(user)
        with self.assertNumQueries(self.expected_queries):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("venues/venue-list.html")

    def test_one_venue(self):
        user = UserFactory(is_superuser=False)
        self.client.force_login(user)
        venue = VenueFactory()
        VenueTapManager.objects.create(venue=venue, user=user)
        with self.assertNumQueries(self.expected_queries):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("venue_table", args=[venue.id]))

    def test_multiple_venues(self):
        user = UserFactory(is_superuser=False)
        self.client.force_login(user)
        for _ in range(2):
            venue = VenueFactory()
            VenueTapManager.objects.create(venue=venue, user=user)
        with self.assertNumQueries(self.expected_queries):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("venues/venue-list.html")

    def test_anonymous_hsv(self):
        with self.settings(IS_ALABAMA_DOT_BEER=False):
            with self.assertNumQueries(0):
                response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("hsv_dot_beer/home.html")
        self.assertNotIn(b"Sorry, your user account is not", response.content)

    def test_anonymous_al(self):
        with self.settings(IS_ALABAMA_DOT_BEER=False):
            with self.assertNumQueries(0):
                response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("hsv_dot_beer/alabama_dot_beer.html")
        self.assertNotIn(b"Sorry, your user account is not", response.content)

    def test_unassigned_hsv(self):
        user = UserFactory(is_superuser=False)
        self.client.force_login(user)
        with self.settings(IS_ALABAMA_DOT_BEER=False):
            with self.assertNumQueries(self.expected_queries):
                response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("hsv_dot_beer/home.html")
        self.assertIn(b"Sorry, your user account is not", response.content)

    def test_unassigned_al(self):
        user = UserFactory(is_superuser=False)
        self.client.force_login(user)
        with self.settings(IS_ALABAMA_DOT_BEER=False):
            with self.assertNumQueries(self.expected_queries):
                response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("hsv_dot_beer/alabama_dot_beer.html")
        self.assertIn(b"Sorry, your user account is not", response.content)
