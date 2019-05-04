from decimal import Decimal
import logging

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from kombu.exceptions import OperationalError

from . import models


LOG = logging.getLogger(__name__)


class UntappdMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UntappdMetadata
        exclude = ('beer', 'id')


class StyleSerializer(serializers.ModelSerializer):
    alternate_names = serializers.StringRelatedField(many=True)

    class Meta:
        model = models.Style
        fields = '__all__'


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Manufacturer
        fields = '__all__'


class ServingSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ServingSize
        # since this is a read-only serializer, exclude id
        exclude = ['id']


class BeerPriceSerializer(serializers.ModelSerializer):
    venue = serializers.StringRelatedField()
    serving_size = ServingSizeSerializer(read_only=True)

    class Meta:
        model = models.BeerPrice
        # since this is a read-only serializer, exclude id and beer
        exclude = ['id', 'beer']


class BeerSerializer(serializers.ModelSerializer):
    manufacturer = ManufacturerSerializer(read_only=True)
    manufacturer_id = serializers.PrimaryKeyRelatedField(
        write_only=True, required=True, allow_null=False,
        queryset=models.Manufacturer.objects.all(),
    )
    abv = serializers.DecimalField(
        max_digits=4, decimal_places=2, min_value=0,
        max_value=Decimal('99.99'), allow_null=True, required=False,
    )
    color_srm = serializers.DecimalField(
        max_digits=4, decimal_places=1, min_value=1,
        # 500 SRM = the darkest specialty grain currently available
        max_value=500, allow_null=True, required=False,
    )
    color_srm_html = serializers.SerializerMethodField()
    style = StyleSerializer(read_only=True)
    venues = serializers.SerializerMethodField()
    prices = BeerPriceSerializer(many=True, read_only=True)
    untappd_metadata = serializers.SerializerMethodField()

    def get_color_srm_html(self, obj):
        return obj.render_srm()

    def get_venues(self, obj):
        from venues.serializers import VenueSerializer
        taps = list(obj.taps.all())
        if not taps:
            return []
        venues = {i.venue for i in taps}
        return VenueSerializer(
            instance=list(sorted(venues, key=lambda v: v.name)),
            many=True,
        ).data

    def validate(self, data):
        try:
            data['manufacturer'] = data.pop('manufacturer_id')
        except KeyError:
            # must be in a patch
            pass
        try:
            data['style'] = data.pop('style_id')
        except KeyError:
            pass
        return data

    def get_untappd_metadata(self, obj):
        from beers.tasks import look_up_beer
        try:
            untappd_metadata = obj.untappd_metadata
        except models.UntappdMetadata.DoesNotExist:
            if obj.untappd_url:
                try:
                    # if it has an untappd URL, queue a lookup for the next in line
                    look_up_beer.delay(obj.id)
                except OperationalError as exc:
                    if str(exc).casefold() == 'max number of clients reached'.casefold():
                        LOG.error('Reached redis limit!')
                    else:
                        raise
            return None
        return UntappdMetadataSerializer(instance=untappd_metadata).data

    class Meta:
        model = models.Beer
        exclude = ('api_vendor_style', 'color_html')
        validators = [
            UniqueTogetherValidator(
                fields=['name', 'manufacturer_id'],
                queryset=models.Beer.objects.all(),
            ),
        ]


class OtherPKSerializer(serializers.Serializer):

    # we'll take care of validating during the view
    id = serializers.IntegerField(min_value=0)
