# Generated by Django 2.2.3 on 2019-07-23 21:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("venues", "0023_auto_20190723_0226"),
    ]

    operations = [
        migrations.AddField(
            model_name="venue",
            name="latitude",
            field=models.DecimalField(
                blank=True, decimal_places=8, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="venue",
            name="longitude",
            field=models.DecimalField(
                blank=True, decimal_places=8, max_digits=11, null=True
            ),
        ),
    ]
