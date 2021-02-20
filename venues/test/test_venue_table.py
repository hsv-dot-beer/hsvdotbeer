from django.test import TestCase
from django.urls import reverse

from hsv_dot_beer.users.test.factories import UserFactory
from beers.test.factories import BeerFactory, ManufacturerFactory, StyleFactory
from beers.models import Beer, Style
from taps.models import Tap
from taps.test.factories import TapFactory
from venues.models import VenueTapManager
from .factories import VenueFactory


class VenueTableTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory()
        cls.normal_user = UserFactory()
        cls.styles = Style.objects.bulk_create(StyleFactory.build_batch(50))
        cls.manufacturer = ManufacturerFactory()
        cls.beers = Beer.objects.bulk_create(
            BeerFactory.build(style=style, manufacturer=cls.manufacturer)
            for style in cls.styles
        )
        cls.taps = Tap.objects.bulk_create(
            TapFactory.build(
                beer=beer,
                venue=cls.venue,
                tap_number=index,
            )
            for index, beer in enumerate(cls.beers)
        )
        VenueTapManager.objects.create(
            user=cls.normal_user,
            venue=cls.venue,
        )

    def setUp(self):
        self.url = reverse("venue_table", args=[self.venue.id])

    def test_normal_user(self):
        self.client.force_login(self.normal_user)
        with self.assertNumQueries(4):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "venues/venue-main.html")
        for beer in self.beers:
            self.assertIn(beer.name, response.content.decode("utf-8"))
            self.assertIn(beer.style.name, response.content.decode("utf-8"))
            self.assertIn(
                f"by {beer.manufacturer.name}", response.content.decode("utf-8")
            )

    def test_user_not_manager(self):
        user = UserFactory()
        self.client.force_login(user)
        with self.assertNumQueries(3):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated(self):
        with self.assertNumQueries(0):
            response = self.client.get(self.url, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(reverse("login")))

    def test_superuser(self):
        user = UserFactory(is_superuser=True)
        self.client.force_login(user)
        with self.assertNumQueries(4):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "venues/venue-main.html")
        for beer in self.beers:
            self.assertIn(beer.name, response.content.decode("utf-8"))
            self.assertIn(
                f"by {beer.manufacturer.name}", response.content.decode("utf-8")
            )
