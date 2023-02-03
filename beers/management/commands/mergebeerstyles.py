"""Merge beer styles.

The script takes one argument: the path to a CSV file.

The format of the file should be:

Column A: Name of the beer style as it exists in the DB
Column B: Name of the beer style that you want it to be
Column C and onwards: Any alternate names for the styles

All style names are case-insensitive but preserving (like a Windows filesystem)

The first row is assumed to be a header.

"""
from argparse import FileType
from csv import reader

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import IntegrityError

from beers.models import Style


class Command(BaseCommand):
    help = "Update styles given the provided .csv file"

    def add_arguments(self, parser):
        parser.add_argument(
            "csvfile",
            help="Path to a CSV file that contains the beer styles",
            type=FileType("r"),
        )

    def handle(self, *args, **options):
        csvfile = options["csvfile"]
        next(csvfile)
        csv = reader(csvfile)
        style_mods = {
            row[0].casefold(): (row[1], tuple(i for i in row[2:] if i)) for row in csv
        }
        styles = Style.objects.prefetch_related(
            "beers",
        ).filter(
            name__in=style_mods,
        )
        names_found = set()
        with transaction.atomic():
            for style in styles.all():
                new_name, alt_names = style_mods[style.name.casefold()]
                if not new_name:
                    # no change requested
                    continue
                old_name = style.name
                names_found.add(old_name.casefold())
                self.stdout.write(f"Renaming {old_name} to {new_name}")
                style.name = new_name
                style.alternate_names.extend(alt_names)
                try:
                    with transaction.atomic():
                        style.save()
                except IntegrityError:
                    self.stderr.write(f"{new_name} already exists. Merging")
                    new_style = Style.objects.get(name=new_name)
                    style.beers.update(style=new_style)
                    style.delete()
                    style = new_style
        styles_missed = set(style_mods.keys()).difference(names_found)
        if styles_missed:
            self.stderr.write(
                self.style.NOTICE(f"Missed styles: {sorted(styles_missed)}")
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully updated all other styles. You can either "
                    "create a new spreadsheet to handle those values or just "
                    "modify them by hand in the admin view"
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("Success!"))
