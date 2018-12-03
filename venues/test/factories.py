import factory
import pytz

from venues.models import Venue, Room


class VenueFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Venue

    name = factory.Sequence(lambda n: f'venue {n}')
    time_zone = factory.Iterator(pytz.all_timezones)


class RoomFactory(factory.django.DjangoModelFactory):
    venue = factory.SubFactory(VenueFactory)
    name = factory.fuzzy.FuzzyText(length=20)

    class Meta:
        model = Room
