from rest_framework import serializers

from . import models

class BeerStyleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BeerStyleCategory
        fields = '__all__'


class BeerStyleTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BeerStyleTag
        fields = '__all__'


class BeerStyleSerializer(serializers.ModelSerializer):
    tags = serializers.StringRelatedField(many=True)
    category = BeerStyleCategorySerializer()

    class Meta:
        model = models.BeerStyle
        fields = '__all__'
