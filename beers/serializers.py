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
    tags = BeerStyleTagSerializer(many=True)
    category = BeerStyleCategorySerializer()

    class Meta:
        model = models.BeerStyle
        fields = '__all__'

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        cat_data = validated_data.pop('category')
        category = models.BeerStyleCategory.objects.create(**cat_data)
        tags = []
        for tag_data in tags_data:
            tags.append(models.BeerStyleTag.objects.create(**tag_data))

        style = models.BeerStyle.objects.create(category=category,
                                                **validated_data)
        style.tags.set(tags)
        return style
