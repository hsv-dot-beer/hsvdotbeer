# Generated by Django 2.1.3 on 2018-12-06 03:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("beers", "0007_auto_20181205_1716"),
    ]

    operations = [
        migrations.CreateModel(
            name="TapListProviderStyleMapping",
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
                    "provider",
                    models.CharField(
                        choices=[
                            ("untappd", "Untappd"),
                            ("digitalpour", "DigitalPour"),
                            ("taphunter", "TapHunter"),
                            ("nook_html", "The Nook's static HTML"),
                            ("manual", "Chalkboard/Whiteboard"),
                            ("", "Unknown"),
                            ("test", "TEST LOCAL PROVIDER"),
                        ],
                        max_length=20,
                    ),
                ),
                ("provider_style_name", models.CharField(max_length=50)),
                (
                    "style",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tap_list_provider_mappings",
                        to="beers.BeerStyle",
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="taplistproviderstylemapping",
            unique_together={("provider", "provider_style_name")},
        ),
    ]
