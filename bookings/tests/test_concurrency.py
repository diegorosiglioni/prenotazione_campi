"""Simultaneous requests (RNF-04): real threads, each with its own database connection."""

import threading

from django.db import connection
from django.test import TransactionTestCase

from accounts.tests.helpers import make_admin, make_member
from bookings.models import Booking
from bookings.services.booking import create_booking
from bookings.tests.helpers import court, rome
from common.clock import fixed_now
from common.errors import DomainError
from courts.models import CourtBlock
from courts.services import block_court

NOW = rome(2026, 10, 20, 10, 0)


def run_together(*tasks):
    """Run the callables at the same moment, one thread each; return their results or exceptions."""
    barrier = threading.Barrier(len(tasks))
    results = [None] * len(tasks)

    def worker(index, task):
        try:
            barrier.wait()
            results[index] = task()
        except Exception as error:  # noqa: BLE001 - the test inspects every outcome
            results[index] = error
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=(i, task)) for i, task in enumerate(tasks)]
    with fixed_now(NOW):
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    return results


class ConcurrencyTestCase(TransactionTestCase):
    # Keep the courts of the data migration after each flush of the database.
    serialized_rollback = True

    def booking_task(self, member, court_code, start):
        target = court(court_code)
        return lambda: create_booking(member, member, target, start)

    def assert_only_domain_errors(self, results, code):
        for result in results:
            if not isinstance(result, Booking):
                self.assertIsInstance(result, DomainError)
                self.assertEqual(result.code, code)


class SimultaneousBookingTests(ConcurrencyTestCase):
    def test_rnf04_same_slot_two_members_one_wins(self):
        mario = make_member(card_code="MARIO")
        lucia = make_member(card_code="LUCIA")
        start = rome(2026, 10, 21, 18, 0)
        results = run_together(
            self.booking_task(mario, "tennis_1", start),
            self.booking_task(lucia, "tennis_1", start),
        )
        self.assertEqual(sum(isinstance(r, Booking) for r in results), 1)
        self.assert_only_domain_errors(results, "slot_taken")
        self.assertEqual(Booking.objects.count(), 1)

    def test_rnf04_same_member_four_requests_max_three(self):
        mario = make_member(card_code="MARIO")
        # Four different courts: only the lock on the member keeps the requests in line.
        requests = [("tennis_1", 21), ("tennis_2", 22), ("basketball", 23), ("bocce", 24)]
        results = run_together(
            *(self.booking_task(mario, code, rome(2026, 10, day, 18, 0)) for code, day in requests)
        )
        self.assertEqual(sum(isinstance(r, Booking) for r in results), 3)
        self.assert_only_domain_errors(results, "limit_reached")
        self.assertEqual(Booking.objects.filter(member=mario).count(), 3)

    def test_rnf04_block_and_booking_together(self):
        admin = make_admin()
        mario = make_member(card_code="MARIO")
        tennis = court("tennis_1")
        start = rome(2026, 10, 21, 18, 0)
        results = run_together(
            self.booking_task(mario, "tennis_1", start),
            lambda: block_court(admin, tennis, rome(2026, 10, 21, 8, 0), rome(2026, 10, 21, 23, 0)),
        )
        self.assertIsInstance(results[1], CourtBlock)
        # Whichever ran first, no active booking is left inside the block.
        self.assertFalse(Booking.objects.filter(court=tennis, status__in=Booking.ACTIVE_STATUSES).exists())
        if not isinstance(results[0], Booking):
            self.assertEqual(results[0].code, "court_blocked")

    def test_rnf04_same_member_two_courts_same_time(self):
        mario = make_member(card_code="MARIO")
        start = rome(2026, 10, 21, 18, 0)
        results = run_together(
            self.booking_task(mario, "tennis_1", start),
            self.booking_task(mario, "tennis_2", start),
        )
        self.assertEqual(sum(isinstance(r, Booking) for r in results), 1)
        self.assert_only_domain_errors(results, "member_overlap")
