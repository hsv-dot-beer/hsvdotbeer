import decimal
import urllib.request
import xml.etree.ElementTree

from django.core.management.base import BaseCommand

from beers.models import BeerStyle, BeerStyleTag, BeerStyleCategory


def parse_subcategory(element):
    """Parse subcategory element of styleguide xml."""
    subcategory = {}
    subcategory_id = element.get('id')

    if subcategory_id[0] in ['C', 'M']:
        subcat_letter = subcategory_id[2]
    else:
        subcat_letter = subcategory_id[1]

    subcategory['subcategory'] = subcat_letter

    for key in ['name', 'aroma', 'appearance', 'flavor', 'mouthfeel',
                'impression', 'comments', 'history', 'ingredients',
                'comparison', 'examples', 'tags']:
        val = element.find(key)
        if val is not None:
            subcategory[key] = val.text

    stats = element.find('stats')
    if stats is not None:
        for key in ['ibu', 'og', 'fg', 'srm', 'abv']:
            stat = stats.find(key)
            if stat is not None:
                if stat.find('low') is not None:
                    subcategory[key + '_low'] = decimal.Decimal(stat.find('low').text)
                if stat.find('high') is not None:
                    subcategory[key + '_high'] = decimal.Decimal(stat.find('high').text)
    return subcategory


def parse_category(element):
    """Parse category element of styleguide xml."""
    category = {
        'name': element.find('name').text,
        'notes': element.find('notes').text,
        'revision': element.find('revision').text,
        'category_id': element.get('id'),
        'entries': [],
    }

    for child in element:
        if child.tag == 'subcategory':
            subcat = parse_subcategory(child)
            category['entries'].append(subcat)
    return category


def parse_class(element):
    """Parse class element of styleguide xml."""
    assert(element.tag == 'class')
    style_class = {
        'name': element.get('type'),
        'entries': [],
    }

    for child in element:
        if child.tag != 'category':
            continue
        style_class['entries'].append(parse_category(child))
    return style_class


def parse_styleguide(element):
    """Parse styleguide element of styleguide xml."""
    assert(element.tag == 'styleguide')
    styles = []
    for child in element:
        styles.append(parse_class(child))
    return styles


def parse_styleguide_xml(filename):
    """Parse XML file into styles."""
    tree = xml.etree.ElementTree.parse(filename)
    root = tree.getroot()
    return parse_styleguide(root)


def parse_styleguide_url(url):
    """Parse url into styles."""
    response = urllib.request.urlopen(url)
    data = response.read()
    tree = xml.etree.ElementTree.fromstring(data)
    return parse_styleguide(tree)


class Command(BaseCommand):
    help = 'Loads beers styles from BJCP Styleguide'

    DEFAULT_URL = 'https://raw.githubusercontent.com/meanphil/bjcp-guidelines-2015/master/styleguide.xml'

    def add_arguments(self, parser):
        parser.add_argument('--url', default=self.DEFAULT_URL)
        parser.add_argument('--clear', action='store_true')

    def make_subcat(self, cat, subcat):
        tags = []
        if 'tags' in subcat:
            tags = [t.strip() for t in subcat['tags'].split(',')]
            del subcat['tags']

        for tag in tags:
            if tag not in self.all_tags:
                t = BeerStyleTag(tag=tag)
                t.save()
                self.all_tags[tag] = t

        bs = BeerStyle(**subcat)
        bs.category = cat
        bs.save()

        if len(tags):
            tags = [self.all_tags[t] for t in tags]
            bs.tags.set(tags)
            bs.save()

        return bs

    def make_category(self, cls, category):
        data = {
            'name': category['name'],
            'category_id': category['category_id'],
            'bjcp_class': cls,
            'notes': category['notes'],
            'revision': category['revision'],
        }
        cat = BeerStyleCategory(**data)
        cat.save()

        subcategories = []
        for subcat in category['entries']:
            subcategories.append(self.make_subcat(cat, subcat))
        return subcategories

    def handle(self, *args, **options):
        if options['clear']:
            BeerStyle.objects.all().delete()
            BeerStyleCategory.objects.all().delete()
            # BeerStyleTag.objects.all().delete()

        styles = parse_styleguide_url(options['url'])
        self.all_tags = BeerStyleTag.objects.in_bulk(field_name='tag')

        all_styles = []
        for style in styles:
            for category in style['entries']:
                all_styles.extend(self.make_category(style['name'], category))

        self.stdout.write(self.style.SUCCESS('Successfully loaded %i styles' % len(all_styles)))
