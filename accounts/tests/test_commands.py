from io import StringIO
from unittest import mock

from django.core.management import CommandError, call_command
from django.test import TestCase

from accounts.models import User
from accounts.tests.helpers import make_admin, make_member

ADMIN_PASSWORD = "admin-password-1"


def run_create_admin(passwords=(ADMIN_PASSWORD, ADMIN_PASSWORD), **options):
    options.setdefault("card_code", "admin")
    options.setdefault("first_name", "Gestore")
    options.setdefault("last_name", "Campi")
    with mock.patch("accounts.management.commands.create_admin.getpass", side_effect=list(passwords)):
        call_command("create_admin", stdout=StringIO(), **options)


class CreateAdminCommandTests(TestCase):
    def test_rf01_create_admin_command(self):
        run_create_admin()
        admin = User.objects.get(role=User.Role.ADMIN)
        self.assertEqual(admin.card_code, "ADMIN")
        self.assertIsNone(admin.card_expiry)
        self.assertIs(admin.must_change_password, False)
        self.assertTrue(admin.check_password(ADMIN_PASSWORD))

    def test_rf01_create_admin_refuses_second_admin(self):
        make_admin(card_code="ADMIN")
        with self.assertRaises(CommandError):
            run_create_admin(card_code="ADMIN2")
        self.assertEqual(User.objects.filter(role=User.Role.ADMIN).count(), 1)

    def test_rf31_create_admin_refuses_code_in_use(self):
        make_member(card_code="ABC1")
        with self.assertRaises(CommandError):
            run_create_admin(card_code="abc1")
        self.assertFalse(User.objects.filter(role=User.Role.ADMIN).exists())

    def test_rf31_create_admin_refuses_invalid_code(self):
        with self.assertRaises(CommandError):
            run_create_admin(card_code="AD-MIN")

    def test_rnf05_create_admin_refuses_short_password(self):
        with self.assertRaises(CommandError):
            run_create_admin(passwords=("corta12", "corta12"))
        self.assertFalse(User.objects.exists())

    def test_rnf05_create_admin_refuses_mismatched_passwords(self):
        with self.assertRaises(CommandError):
            run_create_admin(passwords=(ADMIN_PASSWORD, "altra-password"))
        self.assertFalse(User.objects.exists())

    def test_rf33_changepassword_command_uses_card_code(self):
        admin = make_admin(card_code="ADMIN")
        with mock.patch(
            "django.contrib.auth.management.commands.changepassword.getpass.getpass",
            return_value="nuova-password-1",
        ):
            call_command("changepassword", "ADMIN", stdout=StringIO())
        admin.refresh_from_db()
        self.assertTrue(admin.check_password("nuova-password-1"))
