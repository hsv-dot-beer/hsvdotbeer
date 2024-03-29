import zoneinfo

import factory


from venues.models import Venue


class VenueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Venue

    name = factory.Sequence(lambda n: f"venue {n}")
    time_zone = factory.Iterator(zoneinfo.available_timezones())
    slug = factory.Sequence(lambda n: f"venue-{n}")
