from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from accounts.tests.helpers import make_admin, make_member


class LanguageTests(TestCase):
    def test_rnf02_login_page_italian_by_default(self):
        # The browser's own language does not matter: Italian is the default (RNF-02).
        response = self.client.get(reverse("login"), headers={"accept-language": "en"})
        self.assertContains(response, '<html lang="it">')
        self.assertContains(response, "Codice tessera")

    def test_rnf02_login_page_language_selector(self):
        response = self.client.post(reverse("set_language"), {"language": "en", "next": reverse("login")})
        self.assertRedirects(response, reverse("login"))
        response = self.client.get(reverse("login"))
        self.assertContains(response, '<html lang="en">')
        self.assertContains(response, "Card code")

    def test_rnf02_user_language_after_login(self):
        member = make_member(must_change_password=False, language="en")
        # The selector on the login page says Italian, but after login the user's language wins.
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "it"
        self.client.force_login(member)
        response = self.client.get(reverse("account"))
        self.assertContains(response, '<html lang="en">')

    def test_rf55_member_changes_language(self):
        member = make_member(must_change_password=False)
        self.client.force_login(member)
        response = self.client.post(reverse("account"), {"language": "en"})
        self.assertRedirects(response, reverse("account"), fetch_redirect_response=False)
        member.refresh_from_db()
        self.assertEqual(member.language, "en")
        self.assertContains(self.client.get(reverse("account")), '<html lang="en">')

    def test_rf55_member_cannot_change_other_data(self):
        member = make_member(must_change_password=False)
        self.client.force_login(member)
        self.client.post(
            reverse("account"),
            {
                "language": "en",
                "first_name": "Altro",
                "card_code": "HACK1",
                "card_expiry": "31/12/2099",
                "is_blocked": "",
            },
        )
        member.refresh_from_db()
        self.assertEqual(member.language, "en")
        self.assertEqual(member.first_name, "Mario")
        self.assertEqual(member.card_code, "ABC1")
        self.assertEqual(member.card_expiry.year, 2027)

    def test_rf46_account_page_shows_card_expiry(self):
        member = make_member(must_change_password=False)
        self.client.force_login(member)
        self.assertContains(self.client.get(reverse("account")), "31/12/2027")

    def test_rnf02_admin_changes_own_language(self):
        admin = make_admin()
        self.client.force_login(admin)
        self.client.post(reverse("account"), {"language": "en"})
        admin.refresh_from_db()
        self.assertEqual(admin.language, "en")
