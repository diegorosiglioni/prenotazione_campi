import datetime

from django.test import SimpleTestCase
from django.utils import timezone

import common
from common import now as imported_now
from common.clock import fixed_now

FIXED = datetime.datetime(2026, 3, 29, 6, 0, tzinfo=datetime.timezone.utc)
OTHER = datetime.datetime(2026, 10, 25, 7, 0, tzinfo=datetime.timezone.utc)


class NowTests(SimpleTestCase):
    def test_rnf03_now_is_timezone_aware(self):
        value = common.now()
        self.assertTrue(timezone.is_aware(value))
        real = datetime.datetime.now(datetime.timezone.utc)
        self.assertLess(abs(real - value), datetime.timedelta(seconds=5))

    def test_rnf03_fixed_now_returns_given_instant(self):
        with fixed_now(FIXED):
            self.assertEqual(common.now(), FIXED)
        self.assertNotEqual(common.now(), FIXED)

    def test_rnf03_fixed_now_works_with_direct_import(self):
        with fixed_now(FIXED):
            self.assertEqual(imported_now(), FIXED)

    def test_rnf03_fixed_now_restores_previous_instant(self):
        with fixed_now(FIXED):
            with fixed_now(OTHER):
                self.assertEqual(common.now(), OTHER)
            self.assertEqual(common.now(), FIXED)

    def test_rnf03_fixed_now_rejects_naive_datetime(self):
        with self.assertRaises(ValueError):
            with fixed_now(datetime.datetime(2026, 3, 29, 8, 0)):
                pass
