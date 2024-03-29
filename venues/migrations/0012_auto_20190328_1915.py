# Generated by Django 2.1.7 on 2019-03-28 19:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("venues", "0011_auto_20190222_2231"),
    ]

    operations = [
        migrations.AddField(
            model_name="venue",
            name="email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="venue",
            name="logo_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="venue",
            name="phone_number",
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
