import urllib.request
import xml.etree.ElementTree

from django.core.management.base import BaseCommand, CommandError

from beers.models import BeerStyle


def parse_subcategory(element):
    """Parse subcategory element of styleguide xml."""
    subcategory = {}
    subcategory_id = element.get('id')

    if subcategory_id[0] in ['C', 'M']:
        category_id = subcategory_id[0:2]
        subcat_letter = subcategory_id[2]
    else:
        category_id = subcategory_id[0]
        subcat_letter = subcategory_id[1]

    subcategory['category'] = category_id
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
                    subcategory[key + '_low'] = float(stat.find('low').text)
                if stat.find('high') is not None:
                    subcategory[key + '_high'] = float(stat.find('high').text)
    return subcategory


def parse_category(element):
    """Parse category element of styleguide xml."""
    entries = []
    cat_name = element.find('name').text
    cat_notes = element.find('notes').text
    cat_revision = element.find('revision').text

    for child in element:
        if child.tag == 'subcategory':
            subcat = parse_subcategory(child)
            subcat['category_name'] = cat_name
            subcat['category_notes'] = cat_notes
            subcat['revision'] = cat_revision
            entries.append(subcat)
    return entries


def parse_class(element):
    """Parse class element of styleguide xml."""
    entries = []
    assert(element.tag == 'class')
    style_class = element.get('type')
    for child in element:
        if child.tag != 'category':
            continue
        cat_entries = parse_category(child)
        for entry in cat_entries:
            entry['bjcp_class'] = style_class
            entries.append(entry)
    return entries


def parse_styleguide(element):
    """Parse styleguide element of styleguide xml."""
    assert(element.tag == 'styleguide')
    styles = []
    for child in element:
        styles.extend(parse_class(child))
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

    def handle(self, *args, **options):
        url = 'https://raw.githubusercontent.com/meanphil/bjcp-guidelines-2015/master/styleguide.xml'

        styles = parse_styleguide_url(url)
        for style in styles:
            bs = BeerStyle(**style)
            bs.save()
        self.stdout.write(self.style.SUCCESS('Successfully loaded %i styles' % len(styles)))
