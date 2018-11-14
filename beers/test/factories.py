import factory

from beers.models import BeerStyle

class BeerStyleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BeerStyle

    name = 'Super Light Beer'
    revision = '2015'
    bjcp_class = 'Beer'
    category = '42'
    subcategory = 'A'

    category_name = 'Super Light'
    category_notes = 'Beers for all day football watching'

    ibu_low = 2.2
    ibu_high = 4.2
