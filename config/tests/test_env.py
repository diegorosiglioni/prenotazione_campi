import os
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.env import env_bool, env_list, env_str


class EnvStrTests(SimpleTestCase):
    def test_env_missing_required_variable_raises(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesMessage(ImproperlyConfigured, "DJANGO_SECRET_KEY"):
                env_str("DJANGO_SECRET_KEY")

    def test_env_empty_required_variable_raises(self):
        with mock.patch.dict(os.environ, {"DJANGO_SECRET_KEY": ""}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                env_str("DJANGO_SECRET_KEY")

    def test_env_missing_optional_variable_returns_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(env_str("POSTGRES_HOST", "localhost"), "localhost")

    def test_env_present_variable_returns_value(self):
        with mock.patch.dict(os.environ, {"POSTGRES_HOST": "db"}, clear=True):
            self.assertEqual(env_str("POSTGRES_HOST", "localhost"), "db")


class EnvBoolTests(SimpleTestCase):
    def test_env_bool_accepts_true_false(self):
        cases = {"true": True, "True": True, "1": True, "false": False, "FALSE": False, "0": False}
        for raw, expected in cases.items():
            with self.subTest(raw=raw), mock.patch.dict(os.environ, {"DJANGO_DEBUG": raw}, clear=True):
                self.assertIs(env_bool("DJANGO_DEBUG"), expected)

    def test_env_bool_missing_returns_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIs(env_bool("DJANGO_DEBUG"), False)
            self.assertIs(env_bool("DJANGO_DEBUG", default=True), True)

    def test_env_bool_rejects_other_values(self):
        with mock.patch.dict(os.environ, {"DJANGO_DEBUG": "maybe"}, clear=True):
            with self.assertRaisesMessage(ImproperlyConfigured, "DJANGO_DEBUG"):
                env_bool("DJANGO_DEBUG")


class EnvListTests(SimpleTestCase):
    def test_env_list_splits_on_commas(self):
        with mock.patch.dict(os.environ, {"DJANGO_ALLOWED_HOSTS": "a, b,,c"}, clear=True):
            self.assertEqual(env_list("DJANGO_ALLOWED_HOSTS"), ["a", "b", "c"])

    def test_env_list_missing_or_empty_returns_empty_list(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(env_list("DJANGO_ALLOWED_HOSTS"), [])
        with mock.patch.dict(os.environ, {"DJANGO_ALLOWED_HOSTS": ""}, clear=True):
            self.assertEqual(env_list("DJANGO_ALLOWED_HOSTS"), [])
