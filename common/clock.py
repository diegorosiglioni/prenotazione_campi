"""Single source of the current time, so tests can freeze it (RNF-03)."""

from contextlib import contextmanager

from django.utils import timezone

_fixed_instant = None


def now():
    """Return the current instant as a timezone-aware datetime in UTC."""
    if _fixed_instant is not None:
        return _fixed_instant
    return timezone.now()


@contextmanager
def fixed_now(instant):
    """Make now() return `instant` inside the with-block.

    Works even where now() was imported with `from common import now`.
    """
    global _fixed_instant
    if timezone.is_naive(instant):
        raise ValueError("fixed_now() needs a timezone-aware datetime.")
    previous = _fixed_instant
    _fixed_instant = instant
    try:
        yield instant
    finally:
        _fixed_instant = previous
