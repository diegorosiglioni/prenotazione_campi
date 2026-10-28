from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.tests.helpers import make_admin, make_member
from bookings.models import Booking
from bookings.tests.helpers import court, insert_booking, rome
from common.clock import fixed_now
from courts.models import CourtBlock, CourtType

NOW = rome(2026, 10, 20, 10, 0)


class CourtsPageTests(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.mario = make_member(card_code="MARIO", must_change_password=False)
        self.client.force_login(self.admin)

    def post(self, data):
        with fixed_now(NOW):
            return self.client.post(reverse("staff_courts"), data)

    def test_rf01_member_gets_403_on_courts_admin_page(self):
        self.client.force_login(self.mario)
        self.assertEqual(self.client.get(reverse("staff_courts")).status_code, 403)
        self.assertEqual(self.client.post(reverse("staff_courts"), {"action": "price"}).status_code, 403)

    def test_rf05_page_shows_prices(self):
        response = self.client.get(reverse("staff_courts"))
        for text in ("Calcio", "60,00", "Tennis", "18,00"):
            self.assertContains(response, text)

    def test_rf05_admin_changes_price_page(self):
        tennis = CourtType.objects.get(code="tennis")
        response = self.post({"action": "price", "court_type": tennis.pk, "price": "20,50"})
        self.assertRedirects(response, reverse("staff_courts"), fetch_redirect_response=False)
        tennis.refresh_from_db()
        self.assertEqual(tennis.price, Decimal("20.50"))

    def test_rf05_price_must_be_positive(self):
        tennis = CourtType.objects.get(code="tennis")
        response = self.post({"action": "price", "court_type": tennis.pk, "price": "0"})
        self.assertEqual(response.status_code, 200)
        tennis.refresh_from_db()
        self.assertEqual(tennis.price, Decimal("18.00"))

    def block_data(self, **overrides):
        data = {
            "action": "block",
            "court": court("tennis_1").pk,
            "start_0": "21/10/2026",
            "start_1": "08:00",
            "end_0": "21/10/2026",
            "end_1": "12:00",
        }
        data.update(overrides)
        return data

    def test_rf14_admin_blocks_court_page(self):
        booking = insert_booking(self.mario, "tennis_1", rome(2026, 10, 21, 9, 0))
        response = self.post(self.block_data())
        self.assertRedirects(response, reverse("staff_courts"), fetch_redirect_response=False)
        block = CourtBlock.objects.get()
        self.assertEqual((block.start, block.end), (rome(2026, 10, 21, 8, 0), rome(2026, 10, 21, 12, 0)))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.SYSTEM_CANCELLED)

    def test_rf14_block_in_past_refused_with_message(self):
        response = self.post(self.block_data(start_0="20/10/2026", start_1="09:00"))
        self.assertContains(response, "Questo orario è già passato.")
        self.assertFalse(CourtBlock.objects.exists())

    def test_rf14_block_end_before_start_refused(self):
        response = self.post(self.block_data(end_1="07:00"))
        self.assertContains(response, "La fine deve essere dopo l&#x27;inizio.")
        self.assertFalse(CourtBlock.objects.exists())

    def test_rf14_page_lists_blocks_not_ended(self):
        CourtBlock.objects.create(court=court("bocce"), start=rome(2026, 10, 19, 8), end=rome(2026, 10, 19, 12))
        CourtBlock.objects.create(court=court("bocce"), start=rome(2026, 10, 25, 8), end=rome(2026, 10, 25, 12))
        with fixed_now(NOW):
            response = self.client.get(reverse("staff_courts"))
        self.assertContains(response, "25/10/2026 08:00")
        self.assertNotContains(response, "19/10/2026 08:00")

    def test_rf14_admin_removes_block_page(self):
        block = CourtBlock.objects.create(court=court("bocce"), start=rome(2026, 10, 25, 8), end=rome(2026, 10, 25, 12))
        response = self.post({"action": "remove", "block": block.pk})
        self.assertRedirects(response, reverse("staff_courts"), fetch_redirect_response=False)
        self.assertFalse(CourtBlock.objects.exists())
