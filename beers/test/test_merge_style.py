from django.test import TestCase

from beers.models import Style, StyleAlternateName, Beer

from .factories import BeerFactory, StyleFactory, ManufacturerFactory


class StyleMergeTestCase(TestCase):

    def test_merge_success(self):
        mfg = ManufacturerFactory()
        styles = Style.objects.bulk_create(
            StyleFactory.build() for dummy in range(10)
        )
        Beer.objects.bulk_create(
            BeerFactory.build(style=style, manufacturer=mfg)
            for style in styles
        )
        kept_style = styles[0]
        kept_style.merge_from(styles)
        kept_style.refresh_from_db()
        self.assertEqual(
            kept_style.alternate_names.count(), 9,
        )
        self.assertEqual(
            kept_style.beers.count(), 10,
        )
        self.assertFalse(
            Style.objects.filter(
                id__in=[i.id for i in styles[1:]],
            ).exists()
        )

    def test_merge_duplicate_names(self):
        styles = Style.objects.bulk_create(
            StyleFactory.build() for dummy in range(3)
        )
        StyleAlternateName.objects.bulk_create(
            StyleAlternateName(
                name=i.name, style=styles[0]
            ) for i in styles[1:]
        )
        with self.assertRaises(ValueError):
            styles[0].merge_from(styles)
