# Generated by Django 2.2.3 on 2019-07-14 20:48

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("venues", "0021_auto_20190518_1408"),
    ]

    operations = [
        migrations.AddField(
            model_name="venueapiconfiguration",
            name="taphunter_excluded_lists",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=50),
                blank=True,
                default=list,
                null=True,
                size=None,
            ),
        ),
    ]
