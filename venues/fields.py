"""API fields for venue models

The only reason this exists is that django-timezone-field doesn't include a DRF
model.
"""

from rest_framework.serializers import CharField, ValidationError
import zoneinfo


class TimeZoneField(CharField):
    def to_internal_value(self, value: str) -> zoneinfo.ZoneInfo | str:
        if value:
            try:
                return zoneinfo.ZoneInfo(value)
            except zoneinfo.ZoneInfoNotFoundError:
                raise ValidationError(f"Unknown time zone {value}")
        return ""

    def to_representation(self, value: zoneinfo.ZoneInfo) -> str:
        if value:
            return str(value)
        return ""
