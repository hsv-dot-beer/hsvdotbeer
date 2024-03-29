# Generated by Django 2.2 on 2019-05-03 01:59

from django.db import migrations, transaction
from django.db.utils import IntegrityError


def forwards(apps, schema_editor):
    """Populate alternate names for innerspace because we know in advance
    that they're horribly inconsistent with their beer names"""

    mfg_model = apps.get_model("beers.Manufacturer")
    alt_name_model = apps.get_model("beers.ManufacturerAlternateName")
    beer_model = apps.get_model("beers.Beer")
    if not beer_model.objects.exists():
        # working on an empty dict
        return
    innerspace = mfg_model.objects.get_or_create(name="InnerSpace")[0]
    alt_names = [
        "Innerspace Brewing Company",
        "InnerSpace Brewing co",
        "InnerSpace Brewing  Company",
        "Isb",
    ]
    if not innerspace.alternate_names.exists():
        alt_name_model.objects.bulk_create(
            alt_name_model(name=name, manufacturer=innerspace) for name in alt_names
        )
    else:
        for name in alt_names:
            alt_name_model.objects.get_or_create(
                name=name,
                manufacturer=innerspace,
            )
    try:
        with transaction.atomic():
            beer_model.objects.filter(
                manufacturer__name__in=alt_names,
            ).update(manufacturer=innerspace)
    except IntegrityError:
        # aw, hell, we have an integrity error
        beers_needing_merge = beer_model.objects.filter(
            manufacturer__name__in=alt_names,
        )
        beers_to_keep = {
            beer.name: beer
            for beer in beer_model.objects.filter(
                name__in=[i.name for i in beers_needing_merge],
                manufacturer=innerspace,
            )
        }
        # NOTE: Production is already moderated (only one innerspace),
        # so I can afford to be ultra-lazy here
        for beer in beers_needing_merge:
            try:
                kept_beer = beers_to_keep[beer.name]
            except KeyError:
                beer.manufacturer = innerspace
                beer.save()
            else:
                beer.taps.update(beer=kept_beer)
                beer.delete()
    mfg_model.objects.filter(name__in=alt_names).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("beers", "0026_auto_20190502_0247"),
    ]

    operations = [
        migrations.RunPython(
            forwards,
            migrations.RunPython.noop,
        ),
    ]
