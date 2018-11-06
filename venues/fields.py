"""API fields for venue models

The only reason this exists is that django-timezone-field doesn't include a DRF
model.
"""

from rest_framework.serializers import CharField, ValidationError
import pytz


class TimeZoneField(CharField):

    def to_internal_value(self, value):
        if value:
            try:
                return pytz.timezone(value)
            except pytz.UnknownTimeZoneError:
                raise ValidationError(f'Unknown time zone {value}')
        return ''

    def to_representation(self, value):
        if value:
            return value.zone
        return ''
