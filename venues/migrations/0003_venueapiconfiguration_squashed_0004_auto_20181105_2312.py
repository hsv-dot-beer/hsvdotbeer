# Generated by Django 2.1.3 on 2018-11-05 23:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('venues', '0002_venue_tap_list_provider'),
    ]

    operations = [
        migrations.CreateModel(
            name='VenueAPIConfiguration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField()),
                ('api_key', models.CharField(blank=True, max_length=100)),
                ('venue', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='api_configuration', to='venues.Venue')),
            ],
        ),
    ]
