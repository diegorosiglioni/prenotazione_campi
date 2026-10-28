"""Daylight saving time (RNF-03): the change happens at night, rules use Italian time."""

import datetime

from django.test import TestCase

from accounts.tests.helpers import make_member
from bookings.services.booking import create_booking
from bookings.tests.helpers import court, rome
from common.clock import fixed_now
from common.errors import DomainError

UTC = datetime.timezone.utc


class DaylightSavingTests(TestCase):
    def setUp(self):
        self.mario = make_member(card_code="MARIO")

    def book(self, start, now):
        with fixed_now(now):
            return create_booking(self.mario, self.mario, court("tennis_1"), start)

    def test_rnf03_8am_slot_on_dst_change_days(self):
        # Last Sunday of March 2027: from 28/03 Italy is UTC+2.
        spring = self.book(rome(2027, 3, 28, 8, 0), now=rome(2027, 3, 27, 10, 0))
        self.assertEqual(spring.start, datetime.datetime(2027, 3, 28, 6, 0, tzinfo=UTC))
        self.assertEqual(spring.end - spring.start, datetime.timedelta(hours=1))
        # Last Sunday of October 2026: from 25/10 Italy is UTC+1.
        autumn = self.book(rome(2026, 10, 25, 8, 0), now=rome(2026, 10, 24, 10, 0))
        self.assertEqual(autumn.start, datetime.datetime(2026, 10, 25, 7, 0, tzinfo=UTC))

    def test_rnf03_opening_hours_on_dst_change_days(self):
        for day, now in [((2027, 3, 28), rome(2027, 3, 27, 10)), ((2026, 10, 25), rome(2026, 10, 24, 10))]:
            with self.subTest(day=day):
                with self.assertRaises(DomainError):
                    self.book(rome(*day, 7, 45), now=now)
                self.book(rome(*day, 22, 0), now=now)

    def test_rnf03_window_across_dst_change(self):
        # 20/03/2027 23:30 is still winter time; the last bookable day, 03/04, is summer time.
        self.book(rome(2027, 4, 3, 22, 0), now=rome(2027, 3, 20, 23, 30))
        with self.assertRaises(DomainError) as caught:
            self.book(rome(2027, 4, 4, 8, 0), now=rome(2027, 3, 20, 23, 30))
        self.assertEqual(caught.exception.code, "out_of_window")

    def test_rnf03_today_is_the_italian_date(self):
        # 21/03/2027 00:10 in Italy is still 20/03 in UTC: the window must start from 21/03.
        self.book(rome(2027, 4, 4, 8, 0), now=rome(2027, 3, 21, 0, 10))
