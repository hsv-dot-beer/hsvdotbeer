import factory
import factory.fuzzy

from beers.models import Manufacturer, Beer, Style


class StyleFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "style %d" % n)
    default_color = factory.Sequence(lambda n: f"#{n:0>6X}")

    class Meta:
        model = Style


class ManufacturerFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText(length=40)
    instagram_handle = factory.fuzzy.FuzzyText(length=15)
    twitter_handle = factory.fuzzy.FuzzyText(length=20)

    class Meta:
        model = Manufacturer


class BeerFactory(factory.django.DjangoModelFactory):
    name = factory.fuzzy.FuzzyText(length=20)
    manufacturer = factory.SubFactory(ManufacturerFactory)
    color_srm = factory.Sequence(lambda n: n % 31 + 1)
    style = factory.SubFactory(StyleFactory)

    class Meta:
        model = Beer
