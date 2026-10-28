import datetime

from django.db import transaction

from accounts.models import LoginAttempt, User, normalize_card_code
from audit.services import log_action
from bookings.models import Booking, SystemReason
from bookings.services.booking import cancel_by_system
from common.clock import now

MAX_FAILED_LOGINS = 5
LOGIN_LOCK = datetime.timedelta(minutes=15)


def is_login_locked(card_code):
    """True if the card code had 5 failed logins within 15 minutes, less than 15 minutes ago (RNF-05).

    Attempts made during the lock are not recorded, so the lock ends 15 minutes after the fifth failure.
    """
    recent = list(
        LoginAttempt.objects.filter(card_code=card_code)
        .order_by("-created_at")
        .values_list("created_at", flat=True)[:MAX_FAILED_LOGINS]
    )
    if len(recent) < MAX_FAILED_LOGINS:
        return False
    latest, oldest = recent[0], recent[-1]
    return latest - oldest < LOGIN_LOCK and now() < latest + LOGIN_LOCK


def record_failed_login(card_code):
    LoginAttempt.objects.create(card_code=card_code)


def clear_failed_logins(card_code):
    LoginAttempt.objects.filter(card_code=card_code).delete()


# Admin actions on members (RNF-07): each one runs in a transaction, locks the member's row
# and writes the action log. Passwords never reach the log.

SNAPSHOT_FIELDS = (
    "card_code",
    "first_name",
    "last_name",
    "card_expiry",
    "email",
    "phone",
    "language",
    "is_active",
    "must_change_password",
)

# The language is the member's own choice (RF-55): the admin sets it only at creation.
EDITABLE_FIELDS = ("card_code", "first_name", "last_name", "card_expiry", "email", "phone")


def member_snapshot(member):
    return {field: getattr(member, field) for field in SNAPSHOT_FIELDS}


def _lock(member):
    return User.objects.select_for_update().get(pk=member.pk)


@transaction.atomic
def create_member(actor, data, temporary_password):
    member = User.objects.create_member(password=temporary_password, **data)
    log_action(actor, "user_created", member, after=member_snapshot(member))
    return member


@transaction.atomic
def update_member(actor, member, data):
    member = _lock(member)
    before = member_snapshot(member)
    for field in EDITABLE_FIELDS:
        setattr(member, field, data[field])
    member.card_code = normalize_card_code(member.card_code)
    member.save()
    log_action(actor, "user_updated", member, before=before, after=member_snapshot(member))
    return member


@transaction.atomic
def set_temporary_password(actor, member, password):
    """New temporary password (RF-32, RF-33). Django ends the member's open sessions."""
    member = _lock(member)
    before = member_snapshot(member)
    member.set_password(password)
    member.must_change_password = True
    member.save()
    log_action(actor, "temporary_password_set", member, before=before, after=member_snapshot(member))
    return member


@transaction.atomic
def deactivate_member(actor, member):
    """The account can no longer log in, and its bookings not started yet are cancelled (RF-40)."""
    member = _set_active(actor, member, False, "user_deactivated")
    cancel_by_system(Booking.objects.filter(member=member), SystemReason.ACCOUNT_DEACTIVATED, actor)
    return member


@transaction.atomic
def reactivate_member(actor, member):
    return _set_active(actor, member, True, "user_reactivated")


def _set_active(actor, member, active, action):
    member = _lock(member)
    if member.is_active == active:
        return member
    before = member_snapshot(member)
    member.is_active = active
    member.save()
    log_action(actor, action, member, before=before, after=member_snapshot(member))
    return member
