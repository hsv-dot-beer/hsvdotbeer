from django.db import migrations, models

import os
import xml.etree.ElementTree

dirname = os.path.dirname(__file__)
fixture_dir = os.path.abspath(os.path.join(dirname, '../fixtures'))

def parse_subcategory(element):
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
    assert(element.tag == 'styleguide')
    styles = []
    for child in element:
        styles.extend(parse_class(child))
    return styles

def parse_styleguide_xml(filename):
    tree = xml.etree.ElementTree.parse(filename)
    root = tree.getroot()
    return parse_styleguide(root)

def load_styles(apps, schema_editor):
    BeerStyle = apps.get_model('beers', 'BeerStyle')
    styleguide_file = os.path.join(fixture_dir, 'styleguide.xml')
    styles = parse_styleguide_xml(styleguide_file)

    for style in styles:
        bs = BeerStyle(**style)
        bs.save()

def unload_styles(apps, schema_editor):
    BeerStyle = apps.get_model('beers', 'BeerStyle')
    BeerStyle.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('beers', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_styles, reverse_code=unload_styles)
    ]
