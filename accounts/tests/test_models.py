from django.db import DataError, IntegrityError, transaction
from django.test import TestCase

from accounts.models import User
from accounts.tests.helpers import CARD_EXPIRY, PASSWORD, make_admin, make_member


class UserConstraintTests(TestCase):
    """Direct inserts, without forms or services: the database itself must refuse them."""

    def assert_rejected(self, **fields):
        fields.setdefault("first_name", "Mario")
        fields.setdefault("last_name", "Rossi")
        # DataError: a value longer than the column; IntegrityError: a violated constraint.
        with self.assertRaises((DataError, IntegrityError)), transaction.atomic():
            User.objects.create(**fields)

    def test_rf31_card_code_unique(self):
        User.objects.create(card_code="ABC1", first_name="A", last_name="B", card_expiry=CARD_EXPIRY)
        self.assert_rejected(card_code="ABC1", card_expiry=CARD_EXPIRY)

    def test_rf31_card_code_format_enforced_in_db(self):
        for code in ("abc1", "AB-1", "ÀB1", "", "A" * 21):
            with self.subTest(code=code):
                self.assert_rejected(card_code=code, card_expiry=CARD_EXPIRY)

    def test_rf01_only_one_admin_in_db(self):
        User.objects.create(card_code="ADMIN", first_name="A", last_name="B", role=User.Role.ADMIN)
        self.assert_rejected(card_code="ADMIN2", role=User.Role.ADMIN)

    def test_rf30_member_requires_card_expiry_in_db(self):
        self.assert_rejected(card_code="ABC1", role=User.Role.MEMBER, card_expiry=None)

    def test_rf31_admin_has_no_card_expiry_in_db(self):
        self.assert_rejected(card_code="ADMIN", role=User.Role.ADMIN, card_expiry=CARD_EXPIRY)


class UserManagerTests(TestCase):
    def test_rnf05_password_stored_hashed(self):
        member = make_member()
        self.assertNotEqual(member.password, PASSWORD)
        self.assertTrue(member.check_password(PASSWORD))

    def test_rf31_card_code_saved_uppercase(self):
        member = make_member(card_code=" abc1 ")
        self.assertEqual(member.card_code, "ABC1")

    def test_rf31_lookup_ignores_case(self):
        member = make_member(card_code="ABC1")
        self.assertEqual(User.objects.get_by_natural_key("abc1"), member)

    def test_rf32_new_member_must_change_password(self):
        self.assertIs(make_member().must_change_password, True)

    def test_rf31_admin_has_admin_role_and_no_expiry(self):
        admin = make_admin()
        self.assertEqual(admin.role, User.Role.ADMIN)
        self.assertIsNone(admin.card_expiry)
        self.assertIs(admin.must_change_password, False)
