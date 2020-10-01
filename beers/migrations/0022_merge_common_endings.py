# Generated by Django 2.1.7 on 2019-04-01 01:58
import logging
import re
from django.db import migrations, transaction
from django.db.utils import IntegrityError

LOG = logging.getLogger(__name__)

COMMON_BREWERY_ENDINGS = (
    "Brewing Company",
    "Brewery",
    "Brewing",
    "Brewing Co.",
    "Brewing",
    "Beer Company",
    "Beer",
    "Beer Co.",
    "Craft Brewery",
)

REPLACE_TARGET = "\\."
ENDINGS_REGEX = re.compile(
    f'({"|".join(i.replace(".", REPLACE_TARGET) for i in COMMON_BREWERY_ENDINGS)})$',
    re.IGNORECASE,
)


def merge_common_ending_breweries(apps, schema_editor):
    """Merge breweries whose names end in common endings"""
    mfg_model = apps.get_model("beers.Manufacturer")
    mfgs = mfg_model.objects.all().prefetch_related("beers").order_by("name")
    if not mfgs.exists():
        return
    mfg_dict = {}
    for mfg in mfgs:
        key = ENDINGS_REGEX.sub("", mfg.name.strip()).strip()
        try:
            mfg_dict[key].append(mfg)
        except KeyError:
            mfg_dict[key] = [mfg]
    for short_name, mfg_list in mfg_dict.items():
        if len(mfg_list) == 1:
            if mfg_list[0].name != short_name:
                # we need to shorten the only match
                print(f"Shortening {mfg_list[0].name} to {short_name}")
                mfg_list[0].name = short_name
                try:
                    with transaction.atomic():
                        mfg_list[0].save()
                except IntegrityError:
                    print("Got an integrity error due to case; merging")
                    original = mfg_model.objects.get(name=short_name)
                    merge_mfg(original, mfg_list[0])
                    mfg_list[0] = original
            continue
        # sort the beer list by number of beers for simplicity
        kept = None
        try:
            kept = [i for i in mfg_list if i.name == short_name][0]
        except IndexError:
            mfg_list = sorted(
                mfg_list, key=lambda mfg: len(mfg.beers.all()), reverse=True
            )
            kept = mfg_list[0]
        else:
            mfg_list = sorted(
                (i for i in mfg_list if i != kept),
                key=lambda mfg: len(mfg.beers.all()),
                reverse=True,
            )
        if kept.name != short_name:
            # we need to shorten the only match
            print(f"Shortening {kept.name} to {short_name}")
            kept.name = short_name
            try:
                with transaction.atomic():
                    kept.save()
            except IntegrityError:
                other = mfg_model.objects.get(name=kept.name)
                print(
                    f"Oops, that already exists. Merging instead (keeping PK {other.id} instead of {kept.id})"
                )
                merge_mfg(other, kept)
                kept = other
                print(kept.id)
        for mfg in mfg_list[1:]:
            print("merging mfg %s into %s" % (mfg.name, kept.name))
            merge_mfg(kept, mfg)


class Migration(migrations.Migration):

    dependencies = [
        ("beers", "0021_auto_20190328_2039"),
    ]

    operations = [
        migrations.RunPython(merge_common_ending_breweries, migrations.RunPython.noop),
    ]


def merge_beer(kept_beer, other):
    LOG.info("merging %s into %s", other, kept_beer)
    with transaction.atomic():
        for tap in other.taps.all():
            tap.beer = kept_beer
            tap.save()
        for alternate_name in other.alternate_names.all():
            alternate_name.beer = kept_beer
            alternate_name.save()
        excluded_fields = {
            "name" "in_production",
            "automatic_updates_blocked",
            "manufacturer",
            "id",
        }
        for field in kept_beer._meta.fields:
            field_name = field.name
            if field_name in excluded_fields:
                continue
            other_value = getattr(other, field_name)
            if getattr(kept_beer, field_name) or not other_value:
                # don't overwrite data that's already there
                # or isn't set in the other one
                continue
            setattr(kept_beer, field_name, other_value)
        kept_beer.automatic_updates_blocked = True
        if other.name.casefold() != kept_beer.name.casefold():
            # this will only not happen if manufacturers aren't the same
            BeerAlternateName.objects.update_or_create(
                name=other.name,
                beer=kept_beer,
            )
        other.delete()
        kept_beer.save()


def merge_mfg(kept, other):
    LOG.info("merging %s into %s", other, kept)
    with transaction.atomic():
        other_beers = list(other.beers.all())
        my_beers = {i.name.casefold(): i for i in kept.beers.all()}
        for beer in other_beers:
            beer.manufacturer = kept
            if beer.name.casefold() in my_beers:
                # we have a duplicate beer. Merge those two first.
                # merge_from takes care of saving my_beer and deleting
                # beer
                # keep the one that was already present
                my_beer = my_beers[beer.name.casefold()]
                merge_beer(my_beer, beer)
            else:
                # good
                beer.save()

        excluded_fields = {
            "name",
            "automatic_updates_blocked",
            "id",
        }
        for field in kept._meta.fields:
            field_name = field.name
            if field_name in excluded_fields:
                continue
            other_value = getattr(other, field_name)
            if getattr(kept, field_name) or not other_value:
                # don't overwrite data that's already there
                # or isn't set in the other one
                continue
            setattr(kept, field_name, other_value)
        kept.automatic_updates_blocked = True
        other.delete()
        kept.save()
