# Generated by Django 2.1.7 on 2019-02-26 03:13

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("beers", "0016_beer_stem_and_stein_pk"),
    ]

    operations = [
        migrations.CreateModel(
            name="UntappdMetadata",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("json_data", django.contrib.postgres.fields.jsonb.JSONField()),
                ("timestamp", models.DateTimeField(auto_now=True)),
                (
                    "beer",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="untappd_metadata",
                        to="beers.Beer",
                    ),
                ),
            ],
        ),
    ]
