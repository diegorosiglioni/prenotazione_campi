import datetime
from urllib.parse import urlencode

from django.test import TestCase
from django.urls import reverse

from accounts.tests.helpers import make_admin, make_member
from bookings.models import Booking
from bookings.tests.helpers import court, insert_booking, rome
from common.clock import fixed_now
from courts.models import CourtBlock

NOW = rome(2026, 10, 20, 10, 0)
DAY = datetime.date(2026, 10, 21)


def calendar_url(day=None):
    url = reverse("calendar")
    return f"{url}?date={day.isoformat()}" if day else url


def book_url(court_code, day, time):
    query = urlencode({"court": court_code, "date": day.isoformat(), "time": time})
    return f"{reverse('book')}?{query}"


def escaped(url):
    return url.replace("&", "&amp;")


class PageTestCase(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.mario = make_member(card_code="MARIO", must_change_password=False)
        self.lucia = make_member(
            card_code="LUCIA", first_name="Lucia", last_name="Bianchi", must_change_password=False
        )

    def get(self, url, user, **headers):
        self.client.force_login(user)
        with fixed_now(NOW):
            return self.client.get(url, headers=headers)

    def post(self, url, user, data=None):
        self.client.force_login(user)
        with fixed_now(NOW):
            return self.client.post(url, data or {})


class HomeTests(PageTestCase):
    def test_home_redirects_to_calendar(self):
        for user in (self.mario, self.admin):
            with self.subTest(user=user.card_code):
                response = self.get(reverse("home"), user)
                self.assertRedirects(response, reverse("calendar"), fetch_redirect_response=False)

    def test_calendar_requires_login(self):
        response = self.client.get(reverse("calendar"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('calendar')}")


class CalendarTests(PageTestCase):
    def test_rf11_member_calendar_has_no_names(self):
        insert_booking(self.lucia, "tennis_1", rome(2026, 10, 21, 18, 0))
        response = self.get(calendar_url(DAY), self.mario)
        self.assertContains(response, "Occupato")
        self.assertNotContains(response, "Bianchi")
        self.assertNotContains(response, "LUCIA")

    def test_rf11_member_sees_own_booking(self):
        insert_booking(self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))
        response = self.get(calendar_url(DAY), self.mario)
        self.assertContains(response, "La tua prenotazione")

    def test_rf02_admin_calendar_shows_names_and_status(self):
        insert_booking(self.lucia, "tennis_1", rome(2026, 10, 21, 18, 0))
        response = self.get(calendar_url(DAY), self.admin)
        self.assertContains(response, "Bianchi Lucia")
        self.assertContains(response, "Prenotata")

    def test_rf11_cancelled_booking_shows_free(self):
        insert_booking(self.lucia, "tennis_1", rome(2026, 10, 21, 18, 0), status=Booking.Status.CANCELLED)
        response = self.get(calendar_url(DAY), self.mario)
        self.assertNotContains(response, "Occupato")
        self.assertContains(response, escaped(book_url("tennis_1", DAY, "18:00")))

    def test_rf11_bookable_links_only_where_a_slot_fits(self):
        insert_booking(self.lucia, "tennis_1", rome(2026, 10, 21, 18, 0))
        response = self.get(calendar_url(DAY), self.mario)
        # Free and long enough.
        self.assertContains(response, escaped(book_url("tennis_2", DAY, "18:00")))
        self.assertContains(response, escaped(book_url("football", DAY, "21:30")))
        self.assertContains(response, escaped(book_url("tennis_1", DAY, "17:00")))
        # Occupied, or the slot would cross a booking or 23:00 (RF-04, RF-07).
        self.assertNotContains(response, escaped(book_url("tennis_1", DAY, "18:00")))
        self.assertNotContains(response, escaped(book_url("tennis_1", DAY, "17:15")))
        self.assertNotContains(response, escaped(book_url("football", DAY, "21:45")))
        self.assertNotContains(response, escaped(book_url("tennis_2", DAY, "22:15")))

    def test_rf08_no_links_in_the_past(self):
        response = self.get(calendar_url(NOW.date()), self.mario)
        self.assertNotContains(response, escaped(book_url("tennis_1", NOW.date(), "09:00")))
        self.assertNotContains(response, escaped(book_url("tennis_1", NOW.date(), "10:00")))
        self.assertContains(response, escaped(book_url("tennis_1", NOW.date(), "10:15")))

    def test_rf14_calendar_shows_blocked(self):
        CourtBlock.objects.create(court=court("bocce"), start=rome(2026, 10, 21, 8, 0), end=rome(2026, 10, 21, 12, 0))
        response = self.get(calendar_url(DAY), self.mario)
        self.assertContains(response, "Bloccato")
        self.assertNotContains(response, escaped(book_url("bocce", DAY, "11:30")))
        self.assertContains(response, escaped(book_url("bocce", DAY, "12:00")))

    def test_rf11_htmx_request_returns_grid_only(self):
        response = self.get(calendar_url(DAY), self.mario, HX_Request="true")
        self.assertContains(response, 'id="calendar"')
        self.assertNotContains(response, "<html")
        full = self.get(calendar_url(DAY), self.mario)
        self.assertContains(full, "<html")
        self.assertContains(full, "htmx.min.js")

    def test_rf08_member_calendar_limited_to_window(self):
        too_far = self.get(calendar_url(datetime.date(2026, 11, 5)), self.mario)
        self.assertEqual(too_far.context["day"], datetime.date(2026, 11, 3))
        past = self.get(calendar_url(datetime.date(2026, 10, 1)), self.mario)
        self.assertEqual(past.context["day"], datetime.date(2026, 10, 20))

    def test_admin_calendar_any_day(self):
        for day in (datetime.date(2026, 10, 1), datetime.date(2026, 12, 1)):
            with self.subTest(day=day):
                self.assertEqual(self.get(calendar_url(day), self.admin).context["day"], day)

    def test_calendar_defaults_to_today(self):
        for query in ("", "?date=not-a-date"):
            with self.subTest(query=query):
                response = self.get(reverse("calendar") + query, self.mario)
                self.assertEqual(response.context["day"], datetime.date(2026, 10, 20))


class ConfirmationTests(PageTestCase):
    def test_rf42_confirmation_shows_summary(self):
        response = self.get(book_url("tennis_1", DAY, "18:00"), self.mario)
        for text in ("Tennis 1", "21/10/2026", "18:00", "19:00", "18,00", "Conferma"):
            self.assertContains(response, text)
        self.assertFalse(Booking.objects.exists())

    def test_rf42_member_confirms_booking(self):
        response = self.post(book_url("tennis_1", DAY, "18:00"), self.mario)
        self.assertRedirects(response, reverse("my_bookings"), fetch_redirect_response=False)
        booking = Booking.objects.get()
        self.assertEqual((booking.member, booking.court.code), (self.mario, "tennis_1"))
        self.assertEqual(booking.start, rome(2026, 10, 21, 18, 0))

    def test_rf43_error_message_shown_it_and_en(self):
        for day in (22, 23, 24):
            insert_booking(self.mario, "bocce", rome(2026, 10, day, 18, 0))
        response = self.post(book_url("tennis_1", DAY, "18:00"), self.mario)
        self.assertContains(response, "Hai già 3 prenotazioni attive: è il massimo consentito.")
        self.mario.language = "en"
        self.mario.save()
        response = self.post(book_url("tennis_1", DAY, "18:00"), self.mario)
        self.assertContains(response, "You already have 3 active bookings: that is the maximum allowed.")
        self.assertEqual(Booking.objects.filter(court__code="tennis_1").count(), 0)

    def test_rf43_slot_taken_message(self):
        insert_booking(self.lucia, "tennis_1", rome(2026, 10, 21, 18, 0))
        response = self.post(book_url("tennis_1", DAY, "18:30"), self.mario)
        self.assertContains(response, "Il campo è già occupato in questo orario.")

    def test_invalid_slot_parameters_give_404(self):
        for url in (
            book_url("tennis_9", DAY, "18:00"),
            book_url("tennis_1", DAY, "25:00"),
            f"{reverse('book')}?court=tennis_1",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.get(url, self.mario).status_code, 404)

    def test_admin_books_for_member_offered(self):
        response = self.post(
            book_url("tennis_1", DAY, "18:00"), self.admin, {"member": self.lucia.pk, "offered": "on"}
        )
        self.assertRedirects(response, calendar_url(DAY), fetch_redirect_response=False)
        booking = Booking.objects.get()
        self.assertEqual((booking.member, booking.created_by), (self.lucia, self.admin))
        self.assertEqual(booking.status, Booking.Status.OFFERED)

    def test_rf40_admin_member_list_only_active_members(self):
        self.lucia.is_active = False
        self.lucia.save()
        response = self.get(book_url("tennis_1", DAY, "18:00"), self.admin)
        self.assertContains(response, "Rossi Mario (MARIO)")
        self.assertNotContains(response, "LUCIA")
        response = self.post(book_url("tennis_1", DAY, "18:00"), self.admin, {"member": self.lucia.pk})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Booking.objects.exists())


class MyBookingsTests(PageTestCase):
    def test_rf12_my_bookings_shows_only_own(self):
        insert_booking(self.mario, "tennis_1", rome(2026, 10, 21, 18, 0))
        insert_booking(
            self.mario,
            "bocce",
            rome(2026, 10, 22, 18, 0),
            status=Booking.Status.SYSTEM_CANCELLED,
            system_reason="court_blocked",
        )
        insert_booking(self.mario, "football", rome(2026, 10, 10, 18, 0), status=Booking.Status.NO_SHOW)
        insert_booking(self.lucia, "basketball", rome(2026, 10, 21, 18, 0))
        response = self.get(reverse("my_bookings"), self.mario)
        for text in ("Tennis 1", "Prenotata", "18,00", "Annullata dal sistema", "campo bloccato", "Calcio", "No-show"):
            self.assertContains(response, text)
        self.assertNotContains(response, "Pallacanestro")

    def test_rf31_admin_has_no_bookings_page(self):
        self.assertEqual(self.get(reverse("my_bookings"), self.admin).status_code, 403)
