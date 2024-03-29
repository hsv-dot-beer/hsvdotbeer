# Generated by Django 2.2 on 2019-05-02 02:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("venues", "0016_auto_20190426_1706"),
    ]

    operations = [
        migrations.AlterField(
            model_name="venue",
            name="tap_list_provider",
            field=models.CharField(
                blank=True,
                choices=[
                    ("untappd", "Untappd"),
                    ("digitalpour", "DigitalPour"),
                    ("taphunter", "TapHunter"),
                    ("nook_html", "The Nook's static HTML"),
                    ("manual", "Chalkboard/Whiteboard"),
                    ("", "Unknown"),
                    ("test", "TEST LOCAL PROVIDER"),
                    ("stemandstein", "The Stem & Stein's HTML"),
                    ("taplist.io", "taplist.io"),
                ],
                max_length=30,
                verbose_name="What service the venue uses for digital tap lists",
            ),
        ),
    ]
