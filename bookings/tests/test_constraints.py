"""Rules enforced by the database itself, with direct inserts and no services."""

import datetime
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.tests.helpers import make_member
from bookings.models import Booking
from bookings.tests.helpers import court, insert_booking, rome

START = rome(2026, 11, 5, 18, 0)


class BookingConstraintTests(TestCase):
    def setUp(self):
        self.mario = make_member(card_code="MARIO")
        self.lucia = make_member(card_code="LUCIA")

    def assert_rejected(self, member, court_code, start, **fields):
        with self.assertRaises(IntegrityError), transaction.atomic():
            insert_booking(member, court_code, start, **fields)

    def test_rf07_same_court_overlap_rejected_in_db(self):
        insert_booking(self.mario, "tennis_1", START)
        self.assert_rejected(self.lucia, "tennis_1", START + datetime.timedelta(minutes=30))

    def test_rf07_adjacent_slots_allowed_in_db(self):
        insert_booking(self.mario, "tennis_1", START)
        insert_booking(self.lucia, "tennis_1", START + datetime.timedelta(hours=1))
        insert_booking(self.lucia, "tennis_1", START - datetime.timedelta(hours=1))
        self.assertEqual(Booking.objects.count(), 3)

    def test_rf07_cancelled_booking_frees_slot_in_db(self):
        for status in (Booking.Status.CANCELLED, Booking.Status.ADMIN_CANCELLED, Booking.Status.SYSTEM_CANCELLED):
            insert_booking(self.mario, "tennis_1", START, status=status)
        insert_booking(self.lucia, "tennis_1", START)
        self.assertEqual(Booking.objects.count(), 4)

    def test_rf07_every_occupying_status_blocks_the_court_in_db(self):
        for status in Booking.OCCUPYING_STATUSES:
            with self.subTest(status=status):
                booking = insert_booking(self.mario, "tennis_1", START, status=status)
                self.assert_rejected(self.lucia, "tennis_1", START)
                booking.delete()

    def test_rf07_other_court_same_time_allowed_in_db(self):
        insert_booking(self.mario, "tennis_1", START)
        insert_booking(self.lucia, "tennis_2", START)
        self.assertEqual(Booking.objects.count(), 2)

    def test_rf44_same_member_other_court_rejected_in_db(self):
        insert_booking(self.mario, "tennis_1", START)
        self.assert_rejected(self.mario, "football", START - datetime.timedelta(minutes=45))

    def test_end_after_start_in_db(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Booking.objects.create(
                member=self.mario,
                court=court("bocce"),
                start=START,
                end=START,
                price=Decimal("10.00"),
                created_by=self.mario,
            )

    def test_price_not_negative_in_db(self):
        self.assert_rejected(self.mario, "bocce", START, price=Decimal("-1.00"))
