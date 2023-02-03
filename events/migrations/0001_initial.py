# Generated by Django 2.1.3 on 2018-11-19 18:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("venues", "0003_venueapiconfiguration_squashed_0004_auto_20181105_2312"),
    ]

    operations = [
        migrations.CreateModel(
            name="Event",
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
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                ("title", models.CharField(db_index=True, max_length=50)),
                ("description", models.TextField(blank=True)),
                (
                    "venue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="venues.Venue",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(
                fields=["venue", "start_time"], name="events_even_venue_i_23b7d3_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="event",
            index=models.Index(
                fields=["venue", "end_time"], name="events_even_venue_i_365e6f_idx"
            ),
        ),
    ]
