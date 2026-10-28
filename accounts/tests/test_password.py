from django.test import TestCase
from django.urls import reverse

from accounts.tests.helpers import PASSWORD, make_member

NEW_PASSWORD = "nuova-password-9"


class PasswordChangeTests(TestCase):
    def change_password(self, new_password=NEW_PASSWORD, old_password=PASSWORD):
        return self.client.post(
            reverse("password_change"),
            {"old_password": old_password, "new_password1": new_password, "new_password2": new_password},
        )

    def test_rf32_must_change_password_redirects(self):
        member = make_member(must_change_password=True)
        self.client.force_login(member)
        for name in ("home", "account"):
            with self.subTest(page=name):
                self.assertRedirects(
                    self.client.get(reverse(name)), reverse("password_change"), fetch_redirect_response=False
                )
        self.assertEqual(self.client.get(reverse("password_change")).status_code, 200)

    def test_rf32_logout_allowed_before_change(self):
        member = make_member(must_change_password=True)
        self.client.force_login(member)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("login"))

    def test_rf32_change_clears_flag(self):
        member = make_member(must_change_password=True)
        self.client.force_login(member)
        response = self.change_password()
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        member.refresh_from_db()
        self.assertIs(member.must_change_password, False)
        self.assertTrue(member.check_password(NEW_PASSWORD))
        # The session survives the change and normal pages open again.
        self.assertEqual(self.client.get(reverse("account")).status_code, 200)

    def test_rf32_member_can_change_password_later(self):
        member = make_member(must_change_password=False)
        self.client.force_login(member)
        self.assertEqual(self.client.get(reverse("password_change")).status_code, 200)
        self.change_password()
        member.refresh_from_db()
        self.assertTrue(member.check_password(NEW_PASSWORD))

    def test_rnf05_password_min_8_characters(self):
        member = make_member(must_change_password=True)
        self.client.force_login(member)
        response = self.change_password("abcdefg")
        self.assertEqual(response.status_code, 200)
        member.refresh_from_db()
        self.assertTrue(member.check_password(PASSWORD))
        self.change_password("abcdefgh")
        member.refresh_from_db()
        self.assertTrue(member.check_password("abcdefgh"))

    def test_rf32_anonymous_redirected_to_login(self):
        response = self.client.get(reverse("password_change"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('password_change')}")
