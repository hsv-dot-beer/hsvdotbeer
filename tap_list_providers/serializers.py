from rest_framework import serializers

from beers.serializers import BeerStyleSerializer
from beers.models import BeerStyle
from . import models


class TapListProviderStyleMappingSerializer(serializers.ModelSerializer):

    style = BeerStyleSerializer(read_only=True)
    style_id = serializers.PrimaryKeyRelatedField(
        write_only=True, allow_null=False, required=True,
        queryset=BeerStyle.objects.all(),
    )

    def validate(self, data):
        try:
            data['style'] = data.pop('style_id')
        except KeyError:
            # don't care
            pass
        return data

    class Meta:
        fields = '__all__'
        model = models.TapListProviderStyleMapping
