from unittest import TestCase

from tap_list_providers.base import fix_urls


class URLFixTestCase(TestCase):

    def test_fix_urls(self):
        bad_data = {
            'beer_advocate_url': "http://www.ratebeer.com/beer/ace-pear-cider/3004/",
        }
        fix_urls(bad_data)
        self.assertEqual(
            bad_data,
            {
                'rate_beer_url': "http://www.ratebeer.com/beer/ace-pear-cider/3004/",
            }
        )
