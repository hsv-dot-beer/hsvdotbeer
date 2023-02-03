# Generated by Django 3.0.8 on 2020-10-14 14:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("venues", "0027_auto_20200124_2059"),
    ]

    operations = [
        migrations.AddField(
            model_name="venue",
            name="tap_list_last_check_time",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="The last time the venue's tap list was refreshed",
            ),
        ),
        migrations.AddField(
            model_name="venue",
            name="tap_list_last_update_time",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="The last time the venue's tap list was updated",
            ),
        ),
    ]
