"""Basic beer forms"""

from django.forms import ModelForm, ValidationError, Form, ModelChoiceField

from .models import Beer, Style, Manufacturer


def validate_ibu(value):
    """Enforce limits on IBU"""
    if value is None:
        return
    if value < 0:
        raise ValidationError("IBU cannot be negative")
    if value > 1000:
        raise ValidationError("That's an unreasonably high IBU value.")


def validate_abv(value):
    """Enforce limits on ABV"""
    if value is None:
        return
    if value < 0:
        raise ValidationError("ABV cannot be negative")
    if value > 100:
        raise ValidationError("A beer cannot be more than 100% alcohol")


def validate_srm(value):
    """Enforce limits on color"""
    if value is None:
        return
    if value < 0:
        raise ValidationError("SRM cannot be negative")
    if value > 500:
        raise ValidationError(
            "That's an unreasonably high SRM value."
            " Did you measure pure crude oil by mistake?"
        )


class BeerForm(ModelForm):
    """It's a form for creating and editing beers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["manufacturer"].queryset = Manufacturer.objects.order_by("name")
        self.fields["style"].queryset = Style.objects.order_by("name")

    class Meta:
        model = Beer
        fields = [
            "manufacturer",
            "name",
            "style",
            "in_production",
            "abv",
            "ibu",
            "color_srm",
            "untappd_url",
            "beer_advocate_url",
            "rate_beer_url",
            "logo_url",
            "manufacturer_url",
            "taphunter_url",
        ]
        validators = {
            "abv": validate_abv,
            "ibu": validate_ibu,
            "srm": validate_srm,
        }


class StyleForm(ModelForm):
    """It's a form for creating and editing styles."""

    class Meta:
        model = Style
        fields = [
            "name",
        ]


class ManufacturerSelectForm(Form):
    """Pick a manufacturer, any manufacturer!"""

    manufacturer = ModelChoiceField(
        queryset=Manufacturer.objects.order_by("name"),
        label="Manufacturer/Brewer",
        required=True,
    )
