"""Read settings from environment variables, failing loudly on bad values."""

import os

from django.core.exceptions import ImproperlyConfigured

_REQUIRED = object()
_TRUE_VALUES = {"true", "1"}
_FALSE_VALUES = {"false", "0"}


def env_str(name, default=_REQUIRED):
    """Return the variable's value; an empty value counts as missing."""
    value = os.environ.get(name, "")
    if value:
        return value
    if default is _REQUIRED:
        raise ImproperlyConfigured(f"Missing required environment variable {name}.")
    return default


def env_bool(name, default=False):
    value = os.environ.get(name, "").strip().lower()
    if not value:
        return default
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    raise ImproperlyConfigured(f"Environment variable {name} must be true or false, not {value!r}.")


def env_list(name):
    """Split a comma-separated variable, dropping blank items."""
    value = os.environ.get(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]
