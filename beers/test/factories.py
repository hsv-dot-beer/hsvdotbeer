import factory
import factory.fuzzy

from beers.models import BeerStyle, BeerStyleCategory

CLASS_CHOICES = [x[0] for x in BeerStyleCategory.CLASS_CHOICES]

class BeerStyleCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BeerStyleCategory

    name = factory.Sequence(lambda n: 'style%d' % n)
    bjcp_class = factory.fuzzy.FuzzyChoice(CLASS_CHOICES)
    category_id = factory.Sequence(lambda n: n)


class BeerStyleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BeerStyle

    name = 'Super Light Beer'
    revision = '2015'
    bjcp_class = 'Beer'
    category = BeerStyleCategoryFactory().id
    subcategory = 'A'

    abv_low = factory.fuzzy.FuzzyDecimal(0, 15, precision=1)
    abv_high = factory.fuzzy.FuzzyDecimal(0, 15, precision=1)
