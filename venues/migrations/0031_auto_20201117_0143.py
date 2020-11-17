# Generated by Django 3.1.2 on 2020-11-17 01:43

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("venues", "0030_venueapiconfiguration_arryved_serving_sizes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="venueapiconfiguration",
            name="arryved_serving_sizes",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.TextField(),
                blank=True,
                default=list,
                help_text="Short codes for serving sizes of draft pours",
                null=True,
                size=None,
            ),
        ),
    ]