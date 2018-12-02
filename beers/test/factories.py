import factory
import factory.fuzzy

import string

from beers.models import BeerStyle, BeerStyleCategory, BeerStyleTag

CLASS_CHOICES = [x[0] for x in BeerStyleCategory.CLASS_CHOICES]


class BeerStyleCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BeerStyleCategory

    name = factory.Sequence(lambda n: 'style%d' % n)
    bjcp_class = factory.fuzzy.FuzzyChoice(CLASS_CHOICES)
    category_id = factory.Sequence(lambda n: n)


class BeerStyleTagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BeerStyleTag

    tag = factory.Sequence(lambda n: 'tag%d' % n)


class BeerStyleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BeerStyle

    name = factory.fuzzy.FuzzyText(length=15)
    category = factory.SubFactory(BeerStyleCategoryFactory)
    subcategory = factory.fuzzy.FuzzyText(length=1, chars=string.ascii_uppercase)

    ibu_low = factory.fuzzy.FuzzyInteger(0, 120)
    ibu_high = factory.fuzzy.FuzzyInteger(0, 120)

    srm_low = factory.fuzzy.FuzzyInteger(0, 20)
    srm_high = factory.fuzzy.FuzzyInteger(20, 80)

    og_low = factory.fuzzy.FuzzyDecimal(1.000)
    og_high = factory.fuzzy.FuzzyDecimal(1.200)

    fg_low = factory.fuzzy.FuzzyDecimal(0.900)
    fg_high = factory.fuzzy.FuzzyDecimal(1.030)

    abv_low = factory.fuzzy.FuzzyDecimal(0, 15, precision=1)
    abv_high = factory.fuzzy.FuzzyDecimal(0, 15, precision=1)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if self.ibu_low > self.ibu_high:
            self.ibu_low, self.ibu_high = self.ibu_high, self.ibu_low

        if self.srm_low > self.srm_high:
            self.srm_low, self.srm_high = self.srm_high, self.srm_low

        if self.og_low > self.og_high:
            self.og_low, self.og_high = self.og_high, self.og_low

        if self.fg_low > self.fg_high:
            self.fg_low, self.fg_high = self.fg_high, self.fg_low

        if not create:
            return

        if extracted:
            for tag in extracted:
                self.tags.add(tag)
