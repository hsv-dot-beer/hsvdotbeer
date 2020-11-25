from django.test import TestCase
from django.core.management import call_command


class TestMissingMigrations(TestCase):
    def test_for_missing_migrations(self):
        """Check to see if we're missing migrations in the committed code.

        If no migrations are detected as needed, `result` will be `None`.
        In all other cases, the call will raise a SystemExit, alerting your
        team that someone is trying to make a change that requires a migration
        and that migration is absent.

        Adapted from:
        http://blog.birdhouse.org/2020/11/19/django-testing-for-missing-migrations/
        """

        result = call_command("makemigrations", check=True, dry_run=True)
        self.assertIsNone(result)
