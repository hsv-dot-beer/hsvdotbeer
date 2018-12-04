from unittest import TestCase

from ..utils import render_srm


class SRMTestCase(TestCase):

    def test_none(self):
        self.assertEqual('#ffffff', render_srm(None).lower())

    def test_negative(self):
        self.assertEqual('#ffffff', render_srm(-1).lower())

    def test_above_30(self):
        self.assertEqual(render_srm(30), render_srm(5000))

    def test_not_int(self):
        with self.assertRaises(ValueError):
            render_srm('🦐')
