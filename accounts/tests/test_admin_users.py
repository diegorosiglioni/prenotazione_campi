import datetime
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from accounts import services
from accounts.models import User
from accounts.tests.helpers import PASSWORD, make_admin, make_member
from audit.models import ActionLog
from bookings.models import Booking
from bookings.tests.helpers import insert_booking, rome
from common.clock import fixed_now

TEMPORARY = "temporanea-1"


def member_data(**overrides):
    data = {
        "card_code": "xyz9",
        "first_name": "Lucia",
        "last_name": "Bianchi",
        "card_expiry": "30/06/2027",
        "email": "",
        "phone": "",
        "language": "it",
        "password1": TEMPORARY,
        "password2": TEMPORARY,
    }
    data.update(overrides)
    return data


def update_data(member, **overrides):
    data = {
        "action": "update",
        "card_code": member.card_code,
        "first_name": member.first_name,
        "last_name": member.last_name,
        "card_expiry": member.card_expiry.strftime("%d/%m/%Y"),
        "email": member.email,
        "phone": member.phone,
    }
    data.update(overrides)
    return data


class AdminUserTestCase(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.client.force_login(self.admin)

    def detail_url(self, member):
        return reverse("staff_user_detail", args=[member.pk])


class CreateMemberTests(AdminUserTestCase):
    def create(self, **overrides):
        return self.client.post(reverse("staff_user_create"), member_data(**overrides))

    def test_rf30_admin_creates_member(self):
        response = self.create(email="lucia@example.com", phone="333 1234567")
        member = User.objects.get(card_code="XYZ9")
        self.assertRedirects(response, self.detail_url(member), fetch_redirect_response=False)
        self.assertEqual((member.first_name, member.last_name), ("Lucia", "Bianchi"))
        self.assertEqual(member.card_expiry, datetime.date(2027, 6, 30))
        self.assertEqual(member.role, User.Role.MEMBER)
        self.assertEqual(member.email, "lucia@example.com")

    def test_rf30_email_and_phone_optional(self):
        self.create()
        self.assertTrue(User.objects.filter(card_code="XYZ9").exists())

    def test_rf30_required_fields(self):
        for field in ("card_code", "first_name", "last_name", "card_expiry"):
            with self.subTest(field=field):
                response = self.create(**{field: ""})
                self.assertEqual(response.status_code, 200)
                self.assertFalse(User.objects.filter(role=User.Role.MEMBER).exists())

    def test_rf31_rejects_duplicate_code_any_case(self):
        make_member(card_code="XYZ9")
        response = self.create(card_code="xyz9", first_name="Altra")
        self.assertContains(response, "Questo codice tessera è già in uso.")
        self.assertFalse(User.objects.filter(first_name="Altra").exists())

    def test_rf31_rejects_invalid_code(self):
        for code in ("AB-1", "àb1", "A" * 21):
            with self.subTest(code=code):
                response = self.create(card_code=code)
                self.assertEqual(response.status_code, 200)
                self.assertFalse(User.objects.filter(role=User.Role.MEMBER).exists())

    def test_rf31_member_cannot_take_admin_code(self):
        response = self.create(card_code="admin")
        self.assertContains(response, "Questo codice tessera è già in uso.")

    def test_rf32_new_member_must_change_password(self):
        self.create()
        member = User.objects.get(card_code="XYZ9")
        self.assertIs(member.must_change_password, True)
        self.assertTrue(member.check_password(TEMPORARY))

    def test_rnf05_temporary_password_min_8_characters(self):
        response = self.create(password1="corta12", password2="corta12")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(card_code="XYZ9").exists())

    def test_rf32_temporary_passwords_must_match(self):
        response = self.create(password2="diversa-1")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(card_code="XYZ9").exists())

    def test_rnf02_admin_chooses_language_at_creation(self):
        self.create(language="en")
        self.assertEqual(User.objects.get(card_code="XYZ9").language, "en")


class EditMemberTests(AdminUserTestCase):
    def setUp(self):
        super().setUp()
        self.member = make_member(card_code="ABC1")

    def post(self, data):
        return self.client.post(self.detail_url(self.member), data)

    def test_rf35_admin_updates_card_expiry(self):
        response = self.post(update_data(self.member, card_expiry="31/12/2028"))
        self.assertRedirects(response, self.detail_url(self.member), fetch_redirect_response=False)
        self.member.refresh_from_db()
        self.assertEqual(self.member.card_expiry, datetime.date(2028, 12, 31))

    def test_rf30_admin_updates_member_data(self):
        self.post(update_data(self.member, first_name="Marco", card_code="def2", email="m@example.com"))
        self.member.refresh_from_db()
        self.assertEqual(self.member.first_name, "Marco")
        self.assertEqual(self.member.card_code, "DEF2")
        self.assertEqual(self.member.email, "m@example.com")

    def test_rf31_update_rejects_code_in_use(self):
        make_member(card_code="DEF2")
        response = self.post(update_data(self.member, card_code="def2"))
        self.assertContains(response, "Questo codice tessera è già in uso.")
        self.member.refresh_from_db()
        self.assertEqual(self.member.card_code, "ABC1")

    def test_rf55_admin_does_not_change_language(self):
        self.post(update_data(self.member, language="en"))
        self.member.refresh_from_db()
        self.assertEqual(self.member.language, "it")

    def test_rf33_admin_sets_temporary_password(self):
        self.member.must_change_password = False
        self.member.save()
        response = self.post({"action": "password", "password1": TEMPORARY, "password2": TEMPORARY})
        self.assertRedirects(response, self.detail_url(self.member), fetch_redirect_response=False)
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password(TEMPORARY))
        self.assertIs(self.member.must_change_password, True)

    def test_rf33_temporary_password_ends_member_sessions(self):
        member_client = self.client_class()
        member_client.force_login(self.member)
        self.post({"action": "password", "password1": TEMPORARY, "password2": TEMPORARY})
        response = member_client.get(reverse("account"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('account')}")

    def test_rf40_admin_deactivates_member(self):
        response = self.post({"action": "deactivate"})
        self.assertRedirects(response, self.detail_url(self.member), fetch_redirect_response=False)
        self.member.refresh_from_db()
        self.assertIs(self.member.is_active, False)
        self.client.logout()
        response = self.client.post(reverse("login"), {"username": "ABC1", "password": PASSWORD})
        self.assertContains(response, "Codice tessera o password non corretti.")

    def test_rf40_deactivation_cancels_future_bookings(self):
        now = rome(2026, 10, 20, 10, 0)
        future = insert_booking(self.member, "tennis_1", rome(2026, 10, 21, 18, 0))
        offered = insert_booking(self.member, "bocce", rome(2026, 10, 22, 18, 0), status=Booking.Status.OFFERED)
        started = insert_booking(self.member, "tennis_2", rome(2026, 10, 20, 9, 30))
        past = insert_booking(self.member, "tennis_2", rome(2026, 10, 19, 18, 0))
        with fixed_now(now):
            self.post({"action": "deactivate"})
        for booking in (future, offered):
            booking.refresh_from_db()
            self.assertEqual(booking.status, Booking.Status.SYSTEM_CANCELLED)
            self.assertEqual(booking.system_reason, "account_deactivated")
            self.assertEqual(booking.cancelled_at, now)
            self.assertIsNone(booking.cancelled_by)
        for booking in (started, past):
            booking.refresh_from_db()
            self.assertEqual(booking.status, Booking.Status.BOOKED)
        actions = list(ActionLog.objects.order_by("pk").values_list("action", flat=True))
        self.assertEqual(actions, ["user_deactivated", "booking_system_cancelled", "booking_system_cancelled"])

    def test_rf40_admin_reactivates_member(self):
        self.member.is_active = False
        self.member.save()
        self.post({"action": "reactivate"})
        self.member.refresh_from_db()
        self.assertIs(self.member.is_active, True)

    def test_rf40_deactivated_member_still_listed(self):
        self.member.is_active = False
        self.member.save()
        response = self.client.get(reverse("staff_users"))
        self.assertContains(response, "ABC1")

    def test_rf01_admin_not_listed_nor_editable(self):
        response = self.client.get(reverse("staff_users"))
        self.assertNotContains(response, "ADMIN")
        self.assertEqual(self.client.get(self.detail_url(self.admin)).status_code, 404)

    def test_rf01_user_list_sorted_by_last_name(self):
        make_member(card_code="ZZZ1", last_name="Abate")
        response = self.client.get(reverse("staff_users"))
        content = response.content.decode()
        self.assertLess(content.index("Abate"), content.index("Rossi"))


class AccessTests(TestCase):
    def staff_urls(self, member):
        return [
            reverse("staff_users"),
            reverse("staff_user_create"),
            reverse("staff_user_detail", args=[member.pk]),
        ]

    def test_rf01_member_gets_403_on_admin_pages(self):
        member = make_member(must_change_password=False)
        self.client.force_login(member)
        for url in self.staff_urls(member):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url, {"action": "deactivate"}).status_code, 403)
        member.refresh_from_db()
        self.assertIs(member.is_active, True)

    def test_rf01_anonymous_redirected_to_login(self):
        member = make_member()
        for url in self.staff_urls(member):
            with self.subTest(url=url):
                self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")


class ActionLogTests(AdminUserTestCase):
    def last_log(self):
        return ActionLog.objects.latest("pk")

    def test_rnf07_create_logged(self):
        self.client.post(reverse("staff_user_create"), member_data())
        member = User.objects.get(card_code="XYZ9")
        log = self.last_log()
        self.assertEqual(
            (log.actor, log.action, log.object_type, log.object_id),
            (self.admin, "user_created", "accounts.user", member.pk),
        )
        self.assertIsNone(log.before)
        self.assertEqual(log.after["card_code"], "XYZ9")
        self.assertEqual(log.after["card_expiry"], "2027-06-30")

    def test_rnf07_update_logged_with_before_and_after(self):
        member = make_member(card_code="ABC1")
        self.client.post(self.detail_url(member), update_data(member, card_expiry="31/12/2028"))
        log = self.last_log()
        self.assertEqual(log.action, "user_updated")
        self.assertEqual(log.before["card_expiry"], "2027-12-31")
        self.assertEqual(log.after["card_expiry"], "2028-12-31")

    def test_rnf07_deactivate_and_reactivate_logged(self):
        member = make_member(card_code="ABC1")
        self.client.post(self.detail_url(member), {"action": "deactivate"})
        log = self.last_log()
        self.assertEqual(log.action, "user_deactivated")
        self.assertEqual((log.before["is_active"], log.after["is_active"]), (True, False))
        self.client.post(self.detail_url(member), {"action": "reactivate"})
        self.assertEqual(self.last_log().action, "user_reactivated")

    def test_rnf07_password_never_logged(self):
        member = make_member(card_code="ABC1")
        self.client.post(reverse("staff_user_create"), member_data())
        self.client.post(
            self.detail_url(member), {"action": "password", "password1": TEMPORARY, "password2": TEMPORARY}
        )
        self.assertEqual(self.last_log().action, "temporary_password_set")
        member.refresh_from_db()
        for log in ActionLog.objects.all():
            text = f"{log.before} {log.after}"
            self.assertNotIn(TEMPORARY, text)
            self.assertNotIn(member.password, text)
            self.assertNotIn("pbkdf2", text)

    def test_rnf07_action_and_log_in_same_transaction(self):
        member = make_member(card_code="ABC1")
        with mock.patch.object(services, "log_action", side_effect=RuntimeError("log failed")):
            with self.assertRaises(RuntimeError):
                services.deactivate_member(self.admin, member)
        member.refresh_from_db()
        # The log failed, so the deactivation was rolled back too.
        self.assertIs(member.is_active, True)

    def test_rnf07_no_log_for_own_password_and_language(self):
        member = make_member(card_code="ABC1")
        self.client.force_login(member)
        self.client.post(
            reverse("password_change"),
            {"old_password": PASSWORD, "new_password1": "nuova-pass-1", "new_password2": "nuova-pass-1"},
        )
        self.client.post(reverse("account"), {"language": "en"})
        self.assertFalse(ActionLog.objects.exists())
