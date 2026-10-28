import datetime

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from accounts.models import LoginAttempt
from accounts.tests.helpers import PASSWORD, make_admin, make_member
from common.clock import fixed_now

T0 = datetime.datetime(2026, 7, 10, 18, 0, tzinfo=datetime.timezone.utc)
WRONG_LOGIN = "Codice tessera o password non corretti."
LOCKED = "Troppi tentativi falliti: riprova tra 15 minuti."


class LoginTests(TestCase):
    def setUp(self):
        self.member = make_member(card_code="ABC1", must_change_password=False)

    def login(self, card_code, password=PASSWORD):
        return self.client.post(reverse("login"), {"username": card_code, "password": password})

    def assert_logged_in(self, response, user):
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def assert_refused(self, response, message):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, message)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_rf31_login_any_case(self):
        self.assert_logged_in(self.login("abc1"), self.member)

    def test_rf31_admin_uses_same_form(self):
        admin = make_admin(card_code="ADMIN")
        self.assert_logged_in(self.login("admin"), admin)

    def test_rnf05_wrong_password_and_unknown_code_same_message(self):
        self.assert_refused(self.login("ABC1", "wrong-password"), WRONG_LOGIN)
        self.assert_refused(self.login("ZZZ9"), WRONG_LOGIN)

    def test_rnf05_fifth_failure_locks_code(self):
        with fixed_now(T0):
            for _ in range(5):
                self.assert_refused(self.login("ABC1", "wrong-password"), WRONG_LOGIN)
            # Even the right password is refused while the code is locked.
            self.assert_refused(self.login("ABC1"), LOCKED)

    def test_rnf05_lock_ends_after_15_minutes(self):
        with fixed_now(T0):
            for _ in range(5):
                self.login("ABC1", "wrong-password")
        with fixed_now(T0 + datetime.timedelta(minutes=14, seconds=59)):
            self.assert_refused(self.login("ABC1"), LOCKED)
        with fixed_now(T0 + datetime.timedelta(minutes=15)):
            self.assert_logged_in(self.login("ABC1"), self.member)

    def test_rnf05_four_failures_do_not_lock(self):
        with fixed_now(T0):
            for _ in range(4):
                self.login("ABC1", "wrong-password")
            self.assert_logged_in(self.login("ABC1"), self.member)

    def test_rnf05_failures_older_than_15_minutes_not_counted(self):
        with fixed_now(T0):
            for _ in range(4):
                self.login("ABC1", "wrong-password")
        with fixed_now(T0 + datetime.timedelta(minutes=16)):
            self.assert_refused(self.login("ABC1", "wrong-password"), WRONG_LOGIN)
            self.assert_logged_in(self.login("ABC1"), self.member)

    def test_rnf05_lock_applies_to_unknown_code(self):
        with fixed_now(T0):
            for _ in range(5):
                self.login("ZZZ9")
            self.assert_refused(self.login("ZZZ9"), LOCKED)

    def test_rnf05_lock_is_per_code_any_case(self):
        with fixed_now(T0):
            for _ in range(5):
                self.login("abc1", "wrong-password")
            self.assert_refused(self.login("ABC1"), LOCKED)

    def test_rnf05_attempts_during_lock_not_counted(self):
        with fixed_now(T0):
            for _ in range(5):
                self.login("ABC1", "wrong-password")
        with fixed_now(T0 + datetime.timedelta(minutes=10)):
            self.assert_refused(self.login("ABC1", "wrong-password"), LOCKED)
        self.assertEqual(LoginAttempt.objects.filter(card_code="ABC1").count(), 5)
        with fixed_now(T0 + datetime.timedelta(minutes=15)):
            self.assert_logged_in(self.login("ABC1"), self.member)

    def test_rnf05_success_clears_attempts(self):
        with fixed_now(T0):
            for _ in range(4):
                self.login("ABC1", "wrong-password")
            self.login("ABC1")
        self.assertFalse(LoginAttempt.objects.filter(card_code="ABC1").exists())

    def test_rnf05_session_lasts_30_minutes_of_inactivity(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 30 * 60)
        self.assertIs(settings.SESSION_SAVE_EVERY_REQUEST, True)

    def test_rf40_deactivated_cannot_log_in(self):
        self.member.is_active = False
        self.member.save()
        self.assert_refused(self.login("ABC1"), WRONG_LOGIN)

    def test_rf40_deactivation_ends_open_session(self):
        self.client.force_login(self.member)
        self.member.is_active = False
        self.member.save()
        response = self.client.get(reverse("account"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('account')}")

    def test_rf34_expired_card_can_log_in(self):
        self.member.card_expiry = datetime.date(2020, 1, 1)
        self.member.save()
        self.assert_logged_in(self.login("ABC1"), self.member)

    def test_rf28_blocked_account_can_log_in(self):
        self.member.is_blocked = True
        self.member.save()
        self.assert_logged_in(self.login("ABC1"), self.member)

    def test_rf31_member_lands_on_calendar(self):
        response = self.login("ABC1")
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertRedirects(self.client.get(reverse("home")), reverse("calendar"))

    def test_rf31_admin_lands_on_calendar(self):
        make_admin()
        self.login("ADMIN")
        self.assertRedirects(self.client.get(reverse("home")), reverse("calendar"))

    def test_rf31_logout(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
