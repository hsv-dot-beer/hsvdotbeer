import factory
import factory.fuzzy

from taps.models import Tap
from venues.test.factories import VenueFactory

GAS_CHOICES = [x[0] for x in Tap.GAS_CHOICES]


class TapFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Tap

    venue = factory.SubFactory(VenueFactory)
    tap_number = factory.Sequence(lambda n: n)
    gas_type = factory.fuzzy.FuzzyChoice(GAS_CHOICES)
    estimated_percent_remaining = factory.fuzzy.FuzzyFloat(0, 100)
