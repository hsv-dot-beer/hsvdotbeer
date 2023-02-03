# Generated by Django 2.2.1 on 2019-05-18 14:05

from django.db import migrations


def forwards(apps, schema_editor):
    venue_model = apps.get_model("venues.Venue")
    venue_model.objects.filter(id__in=[1, 3, 4, 7, 13, 14, 17]).update(
        on_downtown_craft_beer_trail=True,
    )
    venue_model.objects.exclude(id__in=[1, 3, 4, 7, 13, 14, 17]).update(
        on_downtown_craft_beer_trail=False,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("venues", "0019_venue_on_downtown_craft_beer_trail"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
