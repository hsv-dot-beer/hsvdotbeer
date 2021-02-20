from django.forms import ModelForm, ValidationError

from beers.models import Beer
from .models import Tap


class TapForm(ModelForm):
    def __init__(self, *args, **kwargs):
        manufacturer = kwargs.pop("manufacturer", None)
        super().__init__(*args, **kwargs)
        if manufacturer:
            self.fields["beer"].queryset = Beer.objects.filter(
                manufacturer=manufacturer,
            )

    def clean_estimated_percent_remaining(self) -> float:
        value = self.cleaned_data["estimated_percent_remaining"]
        if value and value > 100:
            raise ValidationError("A keg cannot be more than 100% full.")
        if value and value < 0:
            raise ValidationError("A keg cannot have negative percent full.")
        if value and value <= 1:
            # convert from decimal percentages to whole percentages
            value *= 100
        return value

    def clean(self):
        cleaned_data = super().clean()
        beer = cleaned_data.get("beer")
        if not beer:
            cleaned_data["estimated_percent_remaining"] = None
            cleaned_data["gas_type"] = ""
        return cleaned_data

    class Meta:
        model = Tap
        exclude = [
            "tap_number",
            "time_added",
            "time_updated",
            "venue",
        ]
