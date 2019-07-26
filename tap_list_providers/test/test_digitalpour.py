"""Test the parsing of digitalpour data"""
import json
import os
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
import responses

from beers.models import Beer, Manufacturer
from venues.test.factories import VenueFactory
from venues.models import Venue, VenueAPIConfiguration
from taps.models import Tap
from tap_list_providers.parsers.digitalpour import DigitalPourParser
from hsv_dot_beer.config.local import BASE_DIR


class CommandsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.venue = VenueFactory(
            tap_list_provider=DigitalPourParser.provider_name)
        cls.venue_cfg = VenueAPIConfiguration.objects.create(
            venue=cls.venue, url='https://localhost:8000',
            digital_pour_venue_id=12345,
            digital_pour_location_number=1,
        )
        with open(os.path.join(
            os.path.dirname(BASE_DIR),
            'tap_list_providers',
            'example_data',
            'rocket_city_craft_beer.json',
        ), 'rb') as json_file:
            cls.json_data = json.loads(json_file.read())

    @responses.activate
    def test_import_digitalpour_data(self):
        """Test parsing the JSON data"""
        responses.add(
            responses.GET,
            DigitalPourParser.URL.format(
                self.venue_cfg.digital_pour_venue_id,
                self.venue_cfg.digital_pour_location_number,
                DigitalPourParser.APIKEY,
            ),
            json=self.json_data,
            status=200,
        )
        self.assertFalse(Tap.objects.exists())
        self.assertEqual(Venue.objects.count(), 1)
        self.assertFalse(Beer.objects.exists())
        self.assertFalse(Manufacturer.objects.exists())
        for dummy in range(2):
            # running twice to make sure we're not double-creating
            args = []
            opts = {}
            call_command('parsedigitalpour', *args, **opts)

            self.assertEqual(Beer.objects.count(), 4, list(Beer.objects.all()))
            self.assertEqual(Manufacturer.objects.count(), 4)
            self.assertEqual(Tap.objects.count(), 4)
            taps = Tap.objects.filter(
                venue=self.venue, tap_number__in=[22, 1, 2],
            ).select_related(
                'beer__style', 'beer__manufacturer',
            ).order_by('tap_number')
            tap = taps[0]
            self.assertEqual(tap.beer.name, 'Hopslam')
            self.assertEqual(
                tap.beer.manufacturer_url,
                'https://www.bellsbeer.com/beer/specialty/hopslam-ale',
            )
            self.assertEqual(
                tap.beer.beer_advocate_url,
                "https://www.beeradvocate.com/beer/profile/287/17112/",
            )
            # RCCB sold Hopslam by the pint but not the growler
            self.assertTrue(
                tap.beer.prices.filter(
                    serving_size__volume_oz=16,
                    venue=self.venue,
                ).exists()
            )
            self.assertFalse(
                tap.beer.prices.filter(
                    serving_size__volume_oz__in=[32, 64],
                    venue=self.venue,
                ).exists()
            )
            self.assertEqual(
                tap.beer.manufacturer.url,
                'http://www.bellsbeer.com/',
            )
            # location nulled out in test data
            self.assertEqual(tap.beer.manufacturer.location, '')
            tap = taps[2]
            self.assertEqual(tap.beer.name, "Milk Stout Nitro")
            self.assertEqual(tap.beer.abv, Decimal('6.0'))
            self.assertEqual(tap.gas_type, 'nitro')
            self.assertEqual(tap.beer.render_srm(), '#241206')
            self.assertEqual(tap.beer.style.name, 'Milk Stout')
            self.assertEqual(tap.beer.manufacturer.twitter_handle, 'LeftHandBrewing')
            prices = {
                Decimal(6.0): Decimal(3.0),
                Decimal(10.0): Decimal(5.0),
                Decimal(16.0): Decimal(8.0),
            }
            price_instances = list(tap.beer.prices.select_related('serving_size', 'venue'))
            self.assertEqual(
                len(price_instances),
                len(prices),
                price_instances,
            )
            for price_instance in price_instances:
                self.assertEqual(price_instance.venue, self.venue, price_instance)
                self.assertIn(price_instance.serving_size.volume_oz, prices, price_instance)
                self.assertEqual(
                    prices[price_instance.serving_size.volume_oz],
                    price_instance.price,
                    price_instance,
                )
            self.assertEqual(
                tap.beer.manufacturer.logo_url,
                'https://s3.amazonaws.com/digitalpourproducerlogos/4f7de8502595f5153887e925.png',
            )
            tap = taps[1]
            # This one has a ResolvedLogoImageUrl but LogoImageUrl is null
            self.assertEqual(tap.beer.name, 'POG Basement')
            self.assertEqual(
                tap.beer.logo_url,
                'https://s3.amazonaws.com/digitalpourproducerlogos/57ac9c3c5e002c172c8a6ede.jpg',
            )

    def test_digital_pour_mead(self):
        tap = {
            'Id': '5c9e54953527260f6c040dc1',
            'MenuItemDisplayDetail': {
                '$type': 'BeerDashboard.Common.Models.Tap, BeerDashboard.Common',  # noqa
                'BeverageType': None,
                'TapType': 'CO2',
                'NonRotating': False,
                'HasMeasuringSystem': False,
                'ParentTapId': None,
                'Material': None,
                'LineDrop': None,
                'LineLength': None,
                'LineDiameter': None,
                'CO2Mix': None,
                'NitroMix': None,
                'PSI': None,
                'Id': '58882be35e002c105cb7e4bc',
                'CompanyId': '57b130dd5e002c0388f8b686',
                'CompanyName': 'Wish You Were Beer',
                'LocationId': '2',
                'LocationName': 'Campus 802',
                'ItemType': 'Tap',
                'DisplayName': '37',
                'DisplayOrder': 37,
                'DisplayLogoUrl': None,
                'DisplayGroup': None,
                'CostCenter': None,
                'NotInUse': False,
                'StorageLocation': {
                    'CompanyId': '57b130dd5e002c0388f8b686',
                    'CompanyName': None,
                    'LocationId': '2',
                    'LocationName': 'Campus 802',
                                    'IsUsable': True,
                                    'DefaultKegLocation': True,
                                    'TemperatureSensorId': None,
                                    'Temperature': 0.0,
                                    'Id': '58882a955e002c105cb7e4ad',
                                    'StorageLocationName': 'Cooler',
                },
                'ProductId': 'H9V0TYD4QY5PT',
                'MeasuringSystemMappingId': None,
                'EventTableId': None,
                'TemperatureSensorId': None,
                'Temperature': 0.0,
                'IsDirty': False,
            },
            'MenuItemProductDetail': {
                '$type': 'BeerDashboard.Common.Models.Keg, BeerDashboard.Common',
                'KegSize': 661.0,
                'KegType': 'CO2',
                'Coupler': 'US Sankey (D)',
                'BatchId': None,
                'DateKegged': None,
                'KegId': None,
                'InitialOuncesConsumed': 153.0,
                'SamplesPoured': 0,
                'SampleSize': 0.0,
                'OuncesConsumed': 196.0,
                'PercentFull': 0.7034795763993948,
                'UseMeasuredValues': False,
                'PosReportedOuncesConsumed': 196.0,
                'PosReportedPercentFull': 0.7034795763993948,
                'MeasuredOuncesConsumed': 0.0,
                'MeasuredPercentFull': 0.0,
                'ShellReturnedToDistributor': False,
                'ShellReturnDate': None,
                'DaysOn': 9,
                'TimeOn': 4067.541096066667,
                'AllowedTaps': None,
                'PercentConsumedBySamples': 0.0,
                'EstimatedOzLeft': 465.0,
                'HasRestrictions': False,
                'RestrictedReplacementsList': None,
                'EstimatedKegLeftDuration': '6.16:50:00',
                'AvailableInBottles': False,
                'MoreKegsAvailable': False,
                'Id': '6d22daf4-3c68-4986-8f32-f57f6e421569',
                'BeverageType': 'Mead',
                'Beverage': {
                    '$type': 'BeerDashboard.Common.Models.MeadModels.Mead, BeerDashboard.Common',  # noqa
                    'BeverageName': 'Passion Fruit Nectar',
                    'Meadery': {
                        'MeaderyName': 'Redstone',
                        'MeaderyUrl': 'http://www.redstonemeadery.com/',
                        'CultureSpecificMeaderyNames': {},
                        'CultureSpecificLocationNames': {},
                        'ProducerName': 'Redstone',
                        'SimplifiedProducerName': 'redstone',
                        'CultureAwareMeaderyName': 'Redstone',
                        'CultureAwareLocationName': 'Boulder, CO',
                        'Id': '52d89988fb890c01246b7835',
                        'FullProducerName': None,
                        'Location': 'Boulder, CO',
                        'ProducersUrl': None,
                        'LogoImageUrl': 'https://s3.amazonaws.com/digitalpourproducerlogos/52d89988fb890c01246b7835.png',  # noqa
                        'TwitterName': '@RedstoneMeadery',
                        'Latitude': 0.0,
                        'Longitude': 0.0,
                        'DefaultKegSize': 1984.0,
                        'DefaultKegCoupler': 'US Sankey (D)',
                        'CompanyId': None,
                        'IsAmateur': False,
                        'AlternateLocations': [],
                    },
                    'Collaborators': [],
                    'MeadName': 'Passion Fruit Nectar',
                    'MeadStyle': {
                        'Id': '52d70daffb890c0f449213d0',
                        'StyleName': 'Session Mead',
                        'ParentId': None,
                        'ParentIds': ['52d5e81cfb890c047453c782'],
                        'Color': 15586620,
                        'RecommendedCO2Mix': None,
                        'RecommendedNitroMix': None,
                        'RecommendedPSI': None,
                        'RecommendedCO2ContentLow': None,
                        'RecommendedCO2ContentHigh': None,
                        'CultureSpecificStyleNames': {},
                        'CultureAwareStyleName': 'Session Mead',
                    },
                    'StyleVariation': 'w/ Passionfruit',
                    'StyleVariationPrefix': None,
                    'Dryness': None,
                    'BarrelAging': None,
                    'HoneyUsed': None,
                    'HopsUsed': None,
                    'Abv': 8.0,
                    'OriginalGravity': None,
                    'FinalGravity': None,
                    'Attributes': None,
                    'MeadUrl': None,
                    'CultureSpecificMeadNames': {},
                    'RateBeerUrl': None,
                    'BeerAdvocateUrl': None,
                    'UntappdUrl': None,
                    'CollaboratorList': '',
                    'BeverageProducer': {
                        '$type': 'BeerDashboard.Common.Models.MeadModels.Meadery, BeerDashboard.Common',  # noqa
                        'MeaderyName': 'Redstone',
                        'MeaderyUrl': 'http://www.redstonemeadery.com/',
                        'CultureSpecificMeaderyNames': {},
                        'CultureSpecificLocationNames': {},
                        'ProducerName': 'Redstone',
                        'SimplifiedProducerName': 'redstone',
                        'CultureAwareMeaderyName': 'Redstone',
                        'CultureAwareLocationName': 'Boulder, CO',
                        'Id': '52d89988fb890c01246b7835',
                        'FullProducerName': None,
                        'Location': 'Boulder, CO',
                        'ProducersUrl': None,
                        'LogoImageUrl': 'https://s3.amazonaws.com/digitalpourproducerlogos/52d89988fb890c01246b7835.png',  # noqa
                        'TwitterName': '@RedstoneMeadery',
                        'Latitude': 0.0,
                        'Longitude': 0.0,
                        'DefaultKegSize': 1984.0,
                        'DefaultKegCoupler': 'US Sankey (D)',
                        'CompanyId': None,
                        'IsAmateur': False,
                        'AlternateLocations': [],
                    },
                    'BeverageStyle': {
                        '$type': 'BeerDashboard.Common.Models.MeadModels.MeadStyle, BeerDashboard.Common',  # noqa
                        'Id': '52d70daffb890c0f449213d0',
                        'StyleName': 'Session Mead',
                        'ParentId': None,
                        'ParentIds': ['52d5e81cfb890c047453c782'],
                        'Color': 15586620,
                        'RecommendedCO2Mix': None,
                        'RecommendedNitroMix': None,
                        'RecommendedPSI': None,
                        'RecommendedCO2ContentLow': None,
                        'RecommendedCO2ContentHigh': None,
                        'CultureSpecificStyleNames': {},
                        'CultureAwareStyleName': 'Session Mead',
                    },
                    'FullMeaderyList': 'Redstone',
                    'ResolvedLogoImageUrl': 'https://s3.amazonaws.com/digitalpourproducerlogos/52d89988fb890c01246b7835.png',  # noqa
                    'FullStyleName': 'Session Mead w/ Passionfruit',
                    'ExpandedStyleName': 'Session Mead w/ Passionfruit',
                    'StyleColor': 15586620,
                    'CultureAwareBeverageName': 'Passion Fruit Nectar',
                    'FullProducerList': 'Redstone',
                    'Id': '55c10a285e002c0bd4aa38d7',
                    'LogoImageUrl': None,
                    'CO2Content': None,
                    'CaloriesPerOz': None,
                    'CustomDescription': None,
                    'CustomStyle': None},
                'DateProduced': '0001-01-01T00:00:00Z',
                'Year': 2019,
                'BeverageCategory': 'Craft',
                'BeverageCategoryLogoUrl': None,
                'Attributes': [],
                'CustomBeverageIcon': None,
                'HasVintage': False,
                'Prices': [
                    {
                        'Id': 'T',
                        'Size': 5.0,
                        'Price': 4.5,
                        'DisplayName': '5oz',
                        'DisplaySize': 5.0,
                        'PosModifier': 'AH4XB7W61363G',
                        'SizeInPos': None,
                        'UPCCode': None,
                        'CostCenter': None,
                        'Glassware': 'Taster',
                        'DisplayOnMenu': True,
                        'Deactivated': False,
                    },
                    {
                        'Id': 'B',
                        'Size': 9.5,
                        'Price': 8.0,
                        'DisplayName': '10oz',
                        'DisplaySize': 10.0,
                        'PosModifier': '0VP4K444GFZV4',
                        'SizeInPos': None,
                        'UPCCode': None,
                        'CostCenter': None,
                        'Glassware': 'Half Snifter',
                        'DisplayOnMenu': True,
                        'Deactivated': False,
                    },
                    {
                        'Id': 'C',
                        'Size': 35.2,
                        'Price': 20.0,
                        'DisplayName': '32oz',
                        'DisplaySize': 32.0,
                        'PosModifier': 'HSA294Z3N388A',
                        'SizeInPos': None,
                        'UPCCode': None,
                        'CostCenter': None,
                        'Glassware': 'Growler (Small)',
                        'DisplayOnMenu': False,
                        'Deactivated': False,
                    },
                    {
                        'Id': 'D',
                        'Size': 70.4,
                        'Price': 40.0,
                        'DisplayName': '64oz',
                        'DisplaySize': 64.0,
                        'PosModifier': 'W517XXS16C6JT',
                        'SizeInPos': None,
                        'UPCCode': None,
                        'CostCenter': None,
                        'Glassware': 'Growler',
                        'DisplayOnMenu': True,
                        'Deactivated': False,
                    },
                ],
                'EventPrices': [
                    {
                        'Id': 'T',
                        'Size': 5.0,
                        'Price': 4.5,
                        'DisplayName': '5oz',
                        'DisplaySize': 5.0,
                        'PosModifier': 'AH4XB7W61363G',
                        'SizeInPos': None,
                        'UPCCode': None,
                        'CostCenter': None,
                        'Glassware': 'Taster',
                        'DisplayOnMenu': True,
                        'Deactivated': False,
                    },
                    {
                        'Id': 'B',
                        'Size': 9.5,
                        'Price': 7.0,
                        'DisplayName': '10oz',
                        'DisplaySize': 10.0,
                        'PosModifier': '0VP4K444GFZV4',
                        'SizeInPos': None,
                        'UPCCode': None,
                        'CostCenter': None,
                        'Glassware': 'Half Snifter',
                        'DisplayOnMenu': True,
                        'Deactivated': False,
                     },
                     {
                        'Id': 'C',
                        'Size': 35.2,
                        'Price': 18.5,
                        'DisplayName': '32oz',
                        'DisplaySize': 32.0,
                        'PosModifier': 'HSA294Z3N388A',
                        'SizeInPos': None,
                        'UPCCode': None,
                        'CostCenter': None,
                        'Glassware': 'Growler (Small)',
                        'DisplayOnMenu': False,
                        'Deactivated': False,
                    },
                    {
                        'Id': 'D',
                        'Size': 70.4,
                        'Price': 37.0,
                        'DisplayName': '64oz',
                        'DisplaySize': 64.0,
                        'PosModifier': 'W517XXS16C6JT',
                        'SizeInPos': None,
                        'UPCCode': None,
                        'CostCenter': None,
                        'Glassware': 'Growler',
                        'DisplayOnMenu': True,
                        'Deactivated': False,
                    },
                ],
                'EventPricesActive': False,
                'EventId': None,
                'EventName': None,
                'DateAdded': '2019-03-30T17:25:53.579Z',
                'DoNotUse': False,
                'ProductFinished': False,
                'ReplacesBeverageIds': [],
                'BeverageNameWithVintage': 'Passion Fruit Nectar',
                'FullBeverageName': 'Redstone Passion Fruit Nectar',
                'FullProducerList': 'Redstone',
                'FullStyleName': 'Session Mead w/ Passionfruit',
                'OverrideableFullStyleName': 'Session Mead w/ Passionfruit',
                'EventItem': False,
                'ReplaceableItem': False,
            },
            'Active': True,
            'EstimatedDatePutOn': None,
            'DatePutOn': '2019-03-29T17:23:35.219Z',
            'DatePulledOff': None,
            'QuantityOnTap': 0,
            'LastRefreshDateTime': '2019-04-04T00:00:15.523Z',
        }
        parser = DigitalPourParser()
        producer = parser.parse_manufacturer(tap)
        self.assertEqual(producer['name'], 'Redstone', producer)
        beer = parser.parse_beer(tap)
        self.assertEqual(beer['name'], 'Passion Fruit Nectar', beer)
