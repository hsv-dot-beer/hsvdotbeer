# Generated by Django 2.2 on 2019-05-03 01:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("venues", "0017_auto_20190502_0224"),
    ]

    operations = [
        migrations.AddField(
            model_name="venueapiconfiguration",
            name="taplist_io_access_code",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="venueapiconfiguration",
            name="taplist_io_display_id",
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
