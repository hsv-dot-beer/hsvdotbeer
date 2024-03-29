# Generated by Django 2.2.2 on 2019-06-09 22:03

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        (
            "tap_list_providers",
            "0001_initial_squashed_0003_delete_taplistproviderstylemapping",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="APIRateLimitTimestamp",
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
                (
                    "api_type",
                    models.CharField(
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
                        max_length=50,
                        unique=True,
                    ),
                ),
                ("rate_limit_expires_at", models.DateTimeField()),
            ],
        ),
    ]
