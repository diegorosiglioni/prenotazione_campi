import datetime
from contextlib import contextmanager
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from accounts.tests.helpers import make_admin, make_member
from audit.models import ActionLog
from bookings.models import Booking
from bookings.services.booking import create_booking
from bookings.tests.helpers import court, insert_booking, rome
from common.clock import fixed_now
from common.errors import DomainError
from courts.models import Court, CourtBlock, CourtType

# The example of RF-08: on 20 October one can book up to 3 November included.
NOW = rome(2026, 10, 20, 10, 0)


class CreateBookingTestCase(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.mario = make_member(card_code="MARIO")
        self.lucia = make_member(card_code="LUCIA")

    def book(self, actor, member, court_code, start, offered=False, now=NOW):
        with fixed_now(now):
            return create_booking(actor, member, court(court_code), start, offered=offered)

    @contextmanager
    def assert_refused(self, code):
        with self.assertRaises(DomainError) as caught:
            yield
        self.assertEqual(caught.exception.code, code)


class OpeningHoursTests(CreateBookingTestCase):
    def test_rf04_start_on_15_minute_steps(self):
        with self.assert_refused("out_of_hours"):
            self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 21, 18, 10))
        booking = self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 21, 18, 15))
        self.assertEqual(booking.start, rome(2026, 10, 21, 18, 15))

    def test_rf04_opening_hours(self):
        with self.assert_refused("out_of_hours"):
            self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 21, 7, 45))
        self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 21, 8, 0))

    def test_rf04_last_start_per_court_type(self):
        self.book(self.mario, self.mario, "football", rome(2026, 10, 21, 21, 30))
        with self.assert_refused("out_of_hours"):
            self.book(self.lucia, self.lucia, "football", rome(2026, 10, 22, 21, 45))
        self.book(self.lucia, self.lucia, "tennis_1", rome(2026, 10, 22, 22, 0))
        with self.assert_refused("out_of_hours"):
            self.book(self.lucia, self.lucia, "tennis_1", rome(2026, 10, 23, 22, 15))

    def test_rf03_end_from_court_type(self):
        football = self.book(self.mario, self.mario, "football", rome(2026, 10, 21, 18, 0))
        tennis = self.book(self.mario, self.mario, "tennis_2", rome(2026, 10, 22, 18, 0))
        self.assertEqual(football.end, rome(2026, 10, 21, 19, 30))
        self.assertEqual(tennis.end, rome(2026, 10, 22, 19, 0))

    def test_rf47_admin_respects_hours(self):
        for court_code, start in [
            ("tennis_1", rome(2026, 10, 21, 7, 45)),
            ("tennis_1", rome(2026, 10, 21, 18, 10)),
            ("football", rome(2026, 10, 21, 21, 45)),
        ]:
            with self.subTest(court=court_code, start=start), self.assert_refused("out_of_hours"):
                self.book(self.admin, self.mario, court_code, start)


class WindowTests(CreateBookingTestCase):
    def test_rf08_rejects_slot_in_past(self):
        for actor in (self.mario, self.admin):
            for start in (rome(2026, 10, 20, 9, 0), NOW):
                with self.subTest(actor=actor.card_code, start=start), self.assert_refused("slot_in_past"):
                    self.book(actor, self.mario, "tennis_1", start)

    def test_rf08_window_last_day_included(self):
        self.book(self.mario, self.mario, "tennis_1", rome(2026, 11, 3, 22, 0))
        with self.assert_refused("out_of_window"):
            self.book(self.mario, self.mario, "tennis_1", rome(2026, 11, 4, 8, 0))

    def test_rf08_admin_not_limited_by_window(self):
        booking = self.book(self.admin, self.mario, "tennis_1", rome(2026, 11, 20, 18, 0))
        self.assertEqual(booking.member, self.mario)


class ActiveLimitTests(CreateBookingTestCase):
    def book_three(self, actor):
        for day in (21, 22, 23):
            self.book(actor, self.mario, "tennis_1", rome(2026, 10, day, 18, 0))

    def test_rf09_fourth_active_booking_rejected(self):
        self.book_three(self.mario)
        with self.assert_refused("limit_reached"):
            self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 24, 18, 0))

    def test_rf09_finished_and_cancelled_do_not_count(self):
        insert_booking(self.mario, "tennis_1", rome(2026, 10, 19, 18, 0))
        insert_booking(self.mario, "bocce", rome(2026, 10, 25, 18, 0), status=Booking.Status.CANCELLED)
        insert_booking(self.mario, "bocce", rome(2026, 10, 26, 18, 0), status=Booking.Status.SYSTEM_CANCELLED)
        insert_booking(self.mario, "bocce", rome(2026, 10, 19, 9, 0), status=Booking.Status.NO_SHOW)
        self.book_three(self.mario)

    def test_rf09_booking_in_progress_counts(self):
        insert_booking(self.mario, "tennis_1", rome(2026, 10, 20, 9, 30))
        self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))
        self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 22, 18, 0))
        with self.assert_refused("limit_reached"):
            self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 23, 18, 0))

    def test_rf09_admin_bookings_count_and_admin_can_exceed(self):
        self.book(self.admin, self.mario, "tennis_1", rome(2026, 10, 21, 18, 0), offered=True)
        self.book(self.admin, self.mario, "tennis_1", rome(2026, 10, 22, 18, 0))
        self.book(self.admin, self.mario, "tennis_1", rome(2026, 10, 23, 18, 0))
        self.book(self.admin, self.mario, "tennis_1", rome(2026, 10, 24, 18, 0))
        with self.assert_refused("limit_reached"):
            self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 25, 18, 0))


class MemberConditionTests(CreateBookingTestCase):
    def test_rf10_blocked_account_rejected(self):
        self.mario.is_blocked = True
        self.mario.save()
        with self.assert_refused("account_blocked"):
            self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))
        self.book(self.admin, self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))

    def test_rf34_expired_card_rejected(self):
        self.mario.card_expiry = datetime.date(2026, 10, 19)
        self.mario.save()
        with self.assert_refused("card_expired"):
            self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 20, 18, 0))

    def test_rf34_card_valid_on_expiry_day(self):
        self.mario.card_expiry = datetime.date(2026, 10, 20)
        self.mario.save()
        self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 20, 18, 0))

    def test_rf34_slot_after_card_expiry_rejected(self):
        self.mario.card_expiry = datetime.date(2026, 10, 25)
        self.mario.save()
        self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 25, 22, 0))
        with self.assert_refused("card_expires_before_slot"):
            self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 26, 8, 0))

    def test_rf34_admin_not_limited_by_card_expiry(self):
        self.mario.card_expiry = datetime.date(2026, 10, 1)
        self.mario.save()
        self.book(self.admin, self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))

    def test_rf40_admin_cannot_book_for_inactive_member(self):
        self.mario.is_active = False
        self.mario.save()
        with self.assert_refused("account_inactive"):
            self.book(self.admin, self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))

    def test_rf31_admin_cannot_be_holder(self):
        with self.assert_refused("not_a_member"):
            self.book(self.admin, self.admin, "tennis_1", rome(2026, 10, 21, 18, 0))

    def test_rf41_member_books_only_for_self(self):
        with self.assertRaises(PermissionDenied):
            self.book(self.mario, self.lucia, "tennis_1", rome(2026, 10, 21, 18, 0))


class OfferedAndPriceTests(CreateBookingTestCase):
    def test_rf23_only_admin_creates_offered(self):
        booking = self.book(self.admin, self.mario, "tennis_1", rome(2026, 10, 21, 18, 0), offered=True)
        self.assertEqual(booking.status, Booking.Status.OFFERED)
        self.assertEqual(booking.price, Decimal("18.00"))
        with self.assertRaises(PermissionDenied):
            self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 22, 18, 0), offered=True)

    def test_rf21_new_booking_is_booked(self):
        booking = self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))
        self.assertEqual(booking.status, Booking.Status.BOOKED)
        self.assertEqual(booking.created_by, self.mario)
        self.assertEqual(booking.created_at, NOW)

    def test_rf05_price_copied_at_creation(self):
        booking = self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))
        CourtType.objects.filter(code="tennis").update(price=Decimal("20.00"))
        booking.refresh_from_db()
        self.assertEqual(booking.price, Decimal("18.00"))
        other = self.book(self.lucia, self.lucia, "tennis_2", rome(2026, 10, 21, 18, 0))
        self.assertEqual(other.price, Decimal("20.00"))


class AvailabilityTests(CreateBookingTestCase):
    def test_rf14_blocked_court_rejected(self):
        CourtBlock.objects.create(court=court("tennis_1"), start=rome(2026, 10, 21, 18, 30), end=rome(2026, 10, 21, 20, 0))
        for actor in (self.mario, self.admin):
            with self.subTest(actor=actor.card_code), self.assert_refused("court_blocked"):
                self.book(actor, self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))
        # A block ending when the slot starts does not touch it.
        self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 21, 20, 0))

    def test_rf14_inactive_court_not_bookable(self):
        Court.objects.filter(code="bocce").update(is_active=False)
        with self.assert_refused("court_blocked"):
            self.book(self.admin, self.mario, "bocce", rome(2026, 10, 21, 18, 0))

    def test_rf07_service_reports_slot_taken(self):
        self.book(self.lucia, self.lucia, "tennis_1", rome(2026, 10, 21, 18, 0))
        for actor in (self.mario, self.admin):
            with self.subTest(actor=actor.card_code), self.assert_refused("slot_taken"):
                self.book(actor, self.mario, "tennis_1", rome(2026, 10, 21, 18, 30))

    def test_rf44_service_reports_member_overlap(self):
        self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))
        for actor in (self.mario, self.admin):
            with self.subTest(actor=actor.card_code), self.assert_refused("member_overlap"):
                self.book(actor, self.mario, "football", rome(2026, 10, 21, 17, 30))


class ActionLogTests(CreateBookingTestCase):
    def test_rnf07_admin_booking_logged(self):
        booking = self.book(self.admin, self.mario, "tennis_1", rome(2026, 10, 21, 18, 0), offered=True)
        entry = ActionLog.objects.get()
        self.assertEqual((entry.actor, entry.action), (self.admin, "booking_created"))
        self.assertEqual((entry.object_type, entry.object_id), ("bookings.booking", booking.pk))
        self.assertEqual(entry.after["status"], "offered")
        self.assertEqual(entry.after["member"], self.mario.pk)

    def test_rnf07_member_booking_not_logged(self):
        self.book(self.mario, self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))
        self.assertFalse(ActionLog.objects.exists())

    def test_rnf07_refused_booking_leaves_nothing(self):
        self.book(self.lucia, self.lucia, "tennis_1", rome(2026, 10, 21, 18, 0))
        with self.assert_refused("slot_taken"):
            self.book(self.admin, self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))
        self.assertEqual(Booking.objects.count(), 1)
        self.assertFalse(ActionLog.objects.exists())
