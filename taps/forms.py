from django.forms import ModelForm

from .models import Tap


class TapForm(ModelForm):
    class Meta:
        model = Tap
        exclude = [
            "tap_number",
            "time_added",
            "time_updated",
            "venue",
        ]
