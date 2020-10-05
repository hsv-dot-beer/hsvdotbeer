# Generated by Django 3.0.1 on 2020-01-12 23:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("beers", "0031_beer_tweeted_about"),
    ]

    operations = [
        migrations.AddField(
            model_name="beer",
            name="beermenus_slug",
            field=models.CharField(blank=True, max_length=250, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="manufacturer",
            name="beermenus_slug",
            field=models.CharField(blank=True, max_length=250, null=True, unique=True),
        ),
    ]
