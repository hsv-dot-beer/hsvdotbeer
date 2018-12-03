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
    category = BeerStyleCategorySerializer(read_only=True)

    category_id = serializers.PrimaryKeyRelatedField(write_only=True,
                                                     queryset=models.BeerStyleCategory.objects.all(),
                                                     required=True, allow_null=False)

    abv_low = serializers.DecimalField(min_value=0, max_value=100, max_digits=3, decimal_places=1, default=0)
    abv_high = serializers.DecimalField(min_value=0, max_value=100, max_digits=3, decimal_places=1, default=0)
    og_low = serializers.DecimalField(min_value=0, max_value=2, max_digits=4, decimal_places=3, default=0)
    og_high = serializers.DecimalField(min_value=0, max_value=2, max_digits=4, decimal_places=3, default=0)
    fg_low = serializers.DecimalField(min_value=0, max_value=2, max_digits=4, decimal_places=3, default=0)
    fg_high = serializers.DecimalField(min_value=0, max_value=2, max_digits=4, decimal_places=3, default=0)

    class Meta:
        model = models.BeerStyle
        fields = '__all__'

    def validate(self, data):
        try:
            data['category'] = data.pop('category_id')
        except KeyError:
            # not specified, which means we're ina PATCH, don't care.
            pass
        for low_field, high_field in [('abv_low', 'abv_high'),
                                      ('ibu_low', 'ibu_high'),
                                      ('og_low', 'og_high'),
                                      ('fg_low', 'fg_high')]:
            try:
                low_value = data[low_field]
                high_value = data[high_field]
                if low_value > high_value:
                    raise serializers.ValidationError(
                        f'{low_field} cannot be greater than {high_field}')
            except KeyError:
                pass
        return data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        tag_names = set(i['tag'] for i in tags)
        existing_tags = list(models.BeerStyleTag.objects.filter(tag__in=tag_names))
        missing_tags = tag_names.difference(set(i.tag for i in existing_tags))
        new_tags = list(models.BeerStyleTag.objects.bulk_create(
            models.BeerStyleTag(tag=i) for i in missing_tags))
        instance = super().create(validated_data)
        instance.tags.set(existing_tags + new_tags)
        return instance

    def update(self, instance, validated_data):
        try:
            tags = validated_data.pop('tags')
        except KeyError:
            return super().update(instance, validated_data)
        tag_names = set(i['tag'] for i in tags)
        existing_tags = list(models.BeerStyleTag.objects.filter(tag__in=tag_names))
        missing_tags = tag_names.difference(set(i.tag for i in existing_tags))
        new_tags = list(models.BeerStyleTag.objects.bulk_create(
            models.BeerStyleTag(tag=i) for i in missing_tags))
        instance = super().update(instance, validated_data)
        instance.tags.set(existing_tags + new_tags, clear=True)
        return instance
