# Generated by Django 2.1.3 on 2018-12-03 22:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("beers", "0004_auto_20181203_2229"),
    ]

    operations = [
        migrations.AddField(
            model_name="beer",
            name="style",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="beers",
                to="beers.BeerStyle",
            ),
        ),
    ]
