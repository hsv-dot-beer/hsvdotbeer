from django.forms import ModelForm

from beers.models import Beer
from .models import Tap


class TapForm(ModelForm):
    def __init__(self, *args, **kwargs):
        manufacturer = kwargs.pop('manufacturer', None)
        super().__init__(*args, **kwargs)
        if manufacturer:
            self.fields["beer"].queryset = Beer.objects.filter(
                manufacturer=manufacturer,
            )

    class Meta:
        model = Tap
        exclude = [
            "tap_number",
            "time_added",
            "time_updated",
            "venue",
        ]
