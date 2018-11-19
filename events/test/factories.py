
import datetime

import factory
from factory.fuzzy import FuzzyText, FuzzyDateTime
from django.utils.timezone import now

from events.models import Event
from venues.test.factories import VenueFactory


class EventFactory(factory.django.DjangoModelFactory):

    venue = factory.SubFactory(VenueFactory)
    title = factory.Sequence(lambda n: f'event {n}')
    description = FuzzyText(length=100)
    host = FuzzyText(length=20)
    # any time before now
    start_time = FuzzyDateTime(
        start_dt=now() - datetime.timedelta(days=30),
    )
    end_time = FuzzyDateTime(
        start_dt=now() + datetime.timedelta(seconds=1),
        end_dt=now() + datetime.timedelta(days=2),
    )

    class Meta:
        model = Event
