from django.db import transaction
from django.db.models import Subquery
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response

from beers.models import Beer

from . import models
from . import serializers


class TapListProviderStyleMappingViewSet(ModelViewSet):
    queryset = models.TapListProviderStyleMapping.objects.all()
    permission_classes = (IsAdminUser, )
    serializer_class = serializers.TapListProviderStyleMappingSerializer

    def create(self, request):
        with transaction.atomic():
            result = super().create(request)
            # update all beers which are assigned to that text style
            Beer.objects.filter(
                api_vendor_style=request.data['provider_style_name'],
                style__isnull=True,
            ).update(
                style_id=result.data['style']['id'],
            )
        return result

    @action(detail=False, methods=['GET'])
    def unmapped(self, request):
        """Get a list of all API-provided styles which are not yet mapped"""
        queryset = Beer.objects.exclude(
            api_vendor_style__in=Subquery(
                models.TapListProviderStyleMapping.objects.values(
                    'provider_style_name',
                ),
            ),
        ).values('api_vendor_style').distinct()
        return Response([{
            'provider_style_name': i['api_vendor_style'],
        } for i in queryset])
