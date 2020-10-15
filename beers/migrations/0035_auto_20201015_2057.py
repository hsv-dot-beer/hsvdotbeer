# Generated by Django 3.0.8 on 2020-10-15 20:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("beers", "0034_auto_20200602_2202"),
    ]

    operations = [
        migrations.AlterField(
            model_name="beer",
            name="logo_url",
            field=models.URLField(
                blank=True, null=True, verbose_name="Beer logo URL (if known)"
            ),
        ),
        migrations.AlterField(
            model_name="beer",
            name="manufacturer_url",
            field=models.URLField(
                blank=True,
                null=True,
                verbose_name="Link to the beer on the manufacturer's website",
            ),
        ),
        migrations.AlterField(
            model_name="beer",
            name="rate_beer_url",
            field=models.URLField(
                blank=True, null=True, verbose_name="RateBeer URL (if known)"
            ),
        ),
        migrations.AlterField(
            model_name="beer",
            name="taphunter_url",
            field=models.URLField(blank=True, null=True, verbose_name="TapHunter URL"),
        ),
        migrations.AlterField(
            model_name="beer",
            name="untappd_url",
            field=models.URLField(
                blank=True, null=True, verbose_name="Untappd URL (if known)"
            ),
        ),
    ]
