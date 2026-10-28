from contextlib import contextmanager
from decimal import Decimal

from django.test import TestCase

from accounts.tests.helpers import make_admin, make_member
from audit.models import ActionLog
from bookings.models import Booking
from bookings.services.booking import create_booking
from bookings.tests.helpers import court, insert_booking, rome
from common.clock import fixed_now
from common.errors import DomainError
from courts import services
from courts.models import CourtBlock, CourtType

NOW = rome(2026, 10, 20, 10, 0)


class CourtServiceTestCase(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.mario = make_member(card_code="MARIO")
        self.lucia = make_member(card_code="LUCIA")

    def block(self, court_code, start, end):
        with fixed_now(NOW):
            return services.block_court(self.admin, court(court_code), start, end)

    def remove(self, block):
        with fixed_now(NOW):
            services.remove_block(self.admin, block)

    def assert_status(self, booking, status):
        booking.refresh_from_db()
        self.assertEqual(booking.status, status)


class PriceTests(CourtServiceTestCase):
    def test_rf05_admin_changes_price(self):
        tennis = CourtType.objects.get(code="tennis")
        with fixed_now(NOW):
            services.set_price(self.admin, tennis, Decimal("20.00"))
        tennis.refresh_from_db()
        self.assertEqual(tennis.price, Decimal("20.00"))
        entry = ActionLog.objects.get()
        self.assertEqual((entry.actor, entry.action, entry.object_id), (self.admin, "price_changed", tennis.pk))
        self.assertEqual((entry.before["price"], entry.after["price"]), ("18.00", "20.00"))


class BlockTests(CourtServiceTestCase):
    @contextmanager
    def assert_refused(self, code):
        with self.assertRaises(DomainError) as caught:
            yield
        self.assertEqual(caught.exception.code, code)

    def test_rf14_block_must_start_in_future(self):
        for start in (rome(2026, 10, 20, 9, 0), NOW):
            with self.subTest(start=start), self.assert_refused("slot_in_past"):
                self.block("tennis_1", start, rome(2026, 10, 20, 12, 0))
        self.assertFalse(CourtBlock.objects.exists())

    def test_rf14_block_spans_several_days(self):
        block = self.block("football", rome(2026, 10, 26, 8, 0), rome(2026, 10, 28, 23, 0))
        self.assertEqual((block.start, block.end), (rome(2026, 10, 26, 8, 0), rome(2026, 10, 28, 23, 0)))

    def test_rf14_block_cancels_overlapping_not_started(self):
        partial = insert_booking(self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))
        inside = insert_booking(self.lucia, "tennis_1", rome(2026, 10, 21, 19, 0), status=Booking.Status.OFFERED)
        adjacent = insert_booking(self.lucia, "tennis_1", rome(2026, 10, 21, 20, 0))
        other_court = insert_booking(self.lucia, "tennis_2", rome(2026, 10, 21, 18, 0))
        self.block("tennis_1", rome(2026, 10, 21, 18, 30), rome(2026, 10, 21, 20, 0))
        for booking in (partial, inside):
            self.assert_status(booking, Booking.Status.SYSTEM_CANCELLED)
            self.assertEqual(booking.system_reason, "court_blocked")
            self.assertEqual(booking.cancelled_at, NOW)
            self.assertIsNone(booking.cancelled_by)
        self.assert_status(adjacent, Booking.Status.BOOKED)
        self.assert_status(other_court, Booking.Status.BOOKED)

    def test_rf14_block_leaves_started_booking(self):
        started = insert_booking(self.mario, "tennis_1", rome(2026, 10, 20, 9, 30))
        self.block("tennis_1", rome(2026, 10, 20, 10, 15), rome(2026, 10, 20, 12, 0))
        self.assert_status(started, Booking.Status.BOOKED)

    def test_rf14_remove_block_does_not_restore(self):
        booking = insert_booking(self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))
        block = self.block("tennis_1", rome(2026, 10, 21, 8, 0), rome(2026, 10, 21, 23, 0))
        self.remove(block)
        self.assertFalse(CourtBlock.objects.exists())
        self.assert_status(booking, Booking.Status.SYSTEM_CANCELLED)
        # The slot can be booked again.
        with fixed_now(NOW):
            create_booking(self.lucia, self.lucia, court("tennis_1"), rome(2026, 10, 21, 18, 0))

    def test_rnf07_block_actions_logged(self):
        booking = insert_booking(self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))
        block = self.block("tennis_1", rome(2026, 10, 21, 8, 0), rome(2026, 10, 21, 23, 0))
        block_pk = block.pk
        self.remove(block)
        entries = list(ActionLog.objects.order_by("pk"))
        self.assertEqual(
            [(e.action, e.object_type, e.object_id) for e in entries],
            [
                ("court_blocked", "courts.courtblock", block_pk),
                ("booking_system_cancelled", "bookings.booking", booking.pk),
                ("court_block_removed", "courts.courtblock", block_pk),
            ],
        )
        self.assertEqual(entries[1].before["status"], "booked")
        self.assertEqual(entries[1].after["status"], "system_cancelled")
        self.assertEqual(entries[2].before["court"], "tennis_1")
