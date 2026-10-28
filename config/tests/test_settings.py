from django.conf import settings
from django.db import connection
from django.test import SimpleTestCase, TestCase


class SettingsTests(SimpleTestCase):
    def test_rnf03_time_zone_is_europe_rome(self):
        self.assertEqual(settings.TIME_ZONE, "Europe/Rome")
        self.assertIs(settings.USE_TZ, True)

    def test_rnf02_italian_default_and_english_available(self):
        self.assertEqual(settings.LANGUAGE_CODE, "it")
        self.assertEqual([code for code, _name in settings.LANGUAGES], ["it", "en"])

    def test_rf45_django_admin_not_installed(self):
        # Django's admin would let data be edited without the service rules.
        self.assertNotIn("django.contrib.admin", settings.INSTALLED_APPS)


class DatabaseTests(TestCase):
    def test_rnf04_tests_run_on_postgresql(self):
        # Exclusion constraints (RF-07, RF-44) exist only on PostgreSQL.
        self.assertEqual(connection.vendor, "postgresql")
        with connection.cursor() as cursor:
            cursor.execute("SHOW server_version")
            version = cursor.fetchone()[0]
        self.assertTrue(version.startswith("18."), version)
