"""Test Reissdorf Kölsch to make sure the name isn't empty"""

from bs4 import BeautifulSoup
from django.test import TestCase


from tap_list_providers.parsers.untappd import UntappdParser


class UntappdBlankNameTestCase(TestCase):
    def setUp(self):
        html = '''
            <div class="item-bg-color menu-item clearfix">
                  <div class="beer">
                   <div class="label-image-hideable beer-label pull-left">
                    <a class="link-font-color" href="https://untappd.com/b/privat-brauerei-heinrich-reissdorf-reissdorf-kolsch/27194" target="_blank">
                     <img alt="Reissdorf Kölsch" src="https://untappd.akamaized.net/site/beer_logos/beer-27194_790cd_sm.jpeg"/>
                    </a>
                   </div>
                   <div class="beer-details item-title-color">
                    <!-- Beer Name + Style -->
                    <p class="beer-name">
                     <a class="item-title-color" href="https://untappd.com/b/privat-brauerei-heinrich-reissdorf-reissdorf-kolsch/27194" target="_blank">
                      <span class="tap-number-hideable">
                      </span>
                      Reissdorf Kölsch
                     </a>
                     <span class="beer-style beer-style-hideable item-title-color">
                      Kölsch
                     </span>
                    </p>
                    <!-- Beer Details -->
                    <div class="item-meta item-title-color">
                     <div class="abv-hideable">
                      <span class="abv">
                       4.8% ABV
                      </span>
                     </div>
                     <div class="ibu-hideable">
                      <span class="ibu">
                       21 IBU
                      </span>
                     </div>
                     <div class="brewery-name-hideable">
                      <span class="brewery">
                       <a class="item-title-color" href="https://untappd.com/brewery/7461" target="_blank">
                        Privat-Brauerei Heinrich Reissdorf
                       </a>
                      </span>
                     </div>
                     <div class="brewery-location-hideable">
                      <span class="location">
                       Köln
                      </span>
                     </div>
                     <div class="rating-hideable">
                      <span class="rating small r350">
                      </span>
                     </div>
                    </div>
                    <!-- Beer Description -->
                    <!-- Beer Container List -->
                    <div class="container-list item-title-color">
                     <div class="with-price">
                      <div class="conatiner-item">
                       <div class="container-row">
                        <span class="type">
                         12oz Bottle
                        </span>
                        <span class="linear-guide">
                        </span>
                        <span class="price">
                         <span class="currency-hideable">
                          $
                         </span>
                         5.50
                        </span>
                       </div>
                      </div>
                     </div>
                     <div class="no-price">
                      <p>
                       <strong>
                        Serving Sizes:
                       </strong>
                       12oz Bottle
                      </p>
                     </div>
                    </div>
                   </div>
                  </div>
                 </div>
        '''   # noqa
        self.tap = BeautifulSoup(html, 'lxml')

    def test_reissdorf_kolsch(self):
        parser = UntappdParser()
        result = parser.parse_tap(self.tap)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['beer']['name'], 'Reissdorf', result)
