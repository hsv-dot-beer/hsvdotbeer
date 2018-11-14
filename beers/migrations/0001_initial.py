# Generated by Django 2.1.3 on 2018-11-05 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BeerStyle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('subcategory', models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'), ('F', 'F'), ('G', 'G'), ('H', 'H'), ('I', 'I'), ('J', 'J'), ('K', 'K'), ('L', 'L'), ('M', 'M'), ('N', 'N'), ('O', 'O'), ('P', 'P'), ('Q', 'Q'), ('R', 'R'), ('S', 'S'), ('T', 'T'), ('U', 'U'), ('V', 'V'), ('W', 'W'), ('X', 'X'), ('Y', 'Y'), ('Z', 'Z')], max_length=1)),
                ('ibu_low', models.PositiveSmallIntegerField(default=0)),
                ('ibu_high', models.PositiveSmallIntegerField(default=0)),
                ('srm_low', models.PositiveSmallIntegerField(default=0)),
                ('srm_high', models.PositiveSmallIntegerField(default=0)),
                ('og_low', models.DecimalField(decimal_places=3, default=0, max_digits=4)),
                ('og_high', models.DecimalField(decimal_places=3, default=0, max_digits=4)),
                ('fg_low', models.DecimalField(decimal_places=3, default=0, max_digits=4)),
                ('fg_high', models.DecimalField(decimal_places=3, default=0, max_digits=4)),
                ('abv_low', models.DecimalField(decimal_places=1, default=0, max_digits=3)),
                ('abv_high', models.DecimalField(decimal_places=1, default=0, max_digits=3)),
                ('aroma', models.TextField(default='')),
                ('appearance', models.TextField(default='')),
                ('flavor', models.TextField(default='')),
                ('mouthfeel', models.TextField(default='')),
                ('impression', models.TextField(default='')),
                ('comments', models.TextField(default='')),
                ('history', models.TextField(default='')),
                ('ingredients', models.TextField(default='')),
                ('comparison', models.TextField(default='')),
                ('examples', models.TextField(default='')),
            ],
        ),
        migrations.CreateModel(
            name='BeerStyleCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100, unique=True)),
                ('bjcp_class', models.CharField(choices=[('beer', 'Beer'), ('cider', 'Cider'), ('mead', 'Mead')], default='beer', max_length=10)),
                ('notes', models.TextField(default='')),
                ('category_id', models.CharField(max_length=2, unique=True)),
                ('revision', models.CharField(default='2015', max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='BeerStyleTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.CharField(db_index=True, max_length=50, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='beerstyle',
            name='category',
            field=models.ForeignKey(on_delete='CASCADE', to='beers.BeerStyleCategory'),
        ),
        migrations.AddField(
            model_name='beerstyle',
            name='tags',
            field=models.ManyToManyField(to='beers.BeerStyleTag'),
        ),
    ]
