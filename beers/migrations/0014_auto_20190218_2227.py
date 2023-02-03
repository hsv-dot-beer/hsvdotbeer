# Generated by Django 2.1.7 on 2019-02-18 22:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("beers", "0013_auto_20190217_2242"),
    ]

    operations = [
        migrations.AddField(
            model_name="beer",
            name="taphunter_url",
            field=models.URLField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="manufacturer",
            name="taphunter_url",
            field=models.URLField(blank=True, null=True, unique=True),
        ),
    ]
