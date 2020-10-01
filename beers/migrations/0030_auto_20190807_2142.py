# Generated by Django 2.2.4 on 2019-08-07 21:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("beers", "0029_merge_20190519_1259"),
    ]

    operations = [
        migrations.AlterField(
            model_name="beerprice",
            name="venue",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="beer_prices",
                to="venues.Venue",
            ),
        ),
    ]
