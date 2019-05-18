import factory
import factory.fuzzy

from beers.models import Manufacturer, Beer, Style, StyleAlternateName


class StyleFactory(factory.django.DjangoModelFactory):

    name = factory.Sequence(lambda n: 'style %d' % n)
    default_color = factory.Sequence(lambda n: '#{:0>6X}'.format(n))

    class Meta:
        model = Style


class StyleAlternateNameFactory(factory.django.DjangoModelFactory):

    name = factory.Sequence(lambda n: 'style alt name %d' % n)

    style = factory.SubFactory(StyleFactory)

    class Meta:
        model = StyleAlternateName


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
