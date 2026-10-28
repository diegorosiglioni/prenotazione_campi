"""Creating bookings and system cancellations (specifiche-tecniche, section 3)."""

import datetime

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.utils import timezone

from accounts.models import User
from audit.services import log_action
from bookings.models import Booking
from common.clock import now
from common.errors import DomainError
from courts.models import Court, CourtBlock

OPENING_TIME = datetime.time(8, 0)
CLOSING_TIME = datetime.time(23, 0)
STEP_MINUTES = 15
WINDOW_DAYS = 14
MAX_ACTIVE_BOOKINGS = 3

# Exclusion constraints of Booking and the error each one means.
CONSTRAINT_ERRORS = {
    "booking_no_court_overlap": "slot_taken",
    "booking_no_member_overlap": "member_overlap",
}


def local_date(instant):
    """The calendar date in Italy, not in UTC (RNF-03)."""
    return timezone.localtime(instant).date()


def today():
    return local_date(now())


def last_bookable_date():
    """Last day a member can book: 14 calendar days from today, included (RF-08)."""
    return today() + datetime.timedelta(days=WINDOW_DAYS)


def within_opening_hours(court_type, start):
    """Start on a 15-minute step from 8:00, end by 23:00 on the same day (RF-04, RF-47)."""
    local_start = timezone.localtime(start)
    local_end = timezone.localtime(start + court_type.slot_length)
    return (
        local_start.minute % STEP_MINUTES == 0
        and local_start.second == 0
        and local_start.microsecond == 0
        and local_start.time() >= OPENING_TIME
        and local_end.date() == local_start.date()
        and local_end.time() <= CLOSING_TIME
    )


def count_active_bookings(member):
    """Booked, paid or offered bookings that have not ended yet (RF-09)."""
    return Booking.objects.filter(member=member, status__in=Booking.ACTIVE_STATUSES, end__gt=now()).count()


def booking_snapshot(booking):
    return {
        "member": booking.member_id,
        "court": booking.court.code,
        "start": booking.start,
        "end": booking.end,
        "price": booking.price,
        "status": booking.status,
        "system_reason": booking.system_reason,
        "cancelled_at": booking.cancelled_at,
    }


@transaction.atomic
def create_booking(actor, member, court, start, offered=False):
    """Book one slot for `member`. The admin books on a member's behalf, without the member's limits.

    Raises DomainError with the code of the broken rule (RF-43).
    """
    by_admin = actor.is_admin
    if not by_admin and (actor.pk != member.pk or offered):
        # Members book only for themselves (RF-41) and never offered bookings (RF-23).
        raise PermissionDenied

    # Lock order user -> court: two requests of the same member run one after the other,
    # so the count of RF-09 is exact; a booking and a court block cannot cross (RF-14, RNF-04).
    member = User.objects.select_for_update().get(pk=member.pk)
    court = Court.objects.select_for_update(of=("self",)).select_related("court_type").get(pk=court.pk)
    court_type = court.court_type
    end = start + court_type.slot_length

    if member.is_admin:
        raise DomainError("not_a_member")
    if not within_opening_hours(court_type, start):
        raise DomainError("out_of_hours")
    if start <= now():
        raise DomainError("slot_in_past")
    if by_admin:
        if not member.is_active:
            raise DomainError("account_inactive")
    else:
        _check_member_rules(member, start)
    if not court.is_active or CourtBlock.objects.filter(court=court, start__lt=end, end__gt=start).exists():
        raise DomainError("court_blocked")

    try:
        # A savepoint: if a constraint fails, the outer transaction stays usable.
        with transaction.atomic():
            booking = Booking.objects.create(
                member=member,
                court=court,
                start=start,
                end=end,
                price=court_type.price,
                status=Booking.Status.OFFERED if offered else Booking.Status.BOOKED,
                created_by=actor,
            )
    except IntegrityError as error:
        code = CONSTRAINT_ERRORS.get(_constraint_name(error))
        if code is None:
            raise
        raise DomainError(code) from error

    if by_admin:
        log_action(actor, "booking_created", booking, after=booking_snapshot(booking))
    return booking


def _check_member_rules(member, start):
    """Limits that apply only when members book for themselves (RF-08, RF-09, RF-10, RF-34, RF-40)."""
    slot_date = local_date(start)
    if slot_date > last_bookable_date():
        raise DomainError("out_of_window")
    if not member.is_active:
        raise DomainError("account_inactive")
    if member.is_blocked:
        raise DomainError("account_blocked")
    if member.card_expiry < today():
        raise DomainError("card_expired")
    if slot_date > member.card_expiry:
        raise DomainError("card_expires_before_slot")
    if count_active_bookings(member) >= MAX_ACTIVE_BOOKINGS:
        raise DomainError("limit_reached")


def _constraint_name(error):
    diag = getattr(error.__cause__, "diag", None)
    return getattr(diag, "constraint_name", None)


def cancel_by_system(bookings, reason, actor=None):
    """Cancel the bookings of `bookings` that have not started yet, with a fixed reason (RF-14, RF-28, RF-40).

    Call it inside the caller's transaction, after locking the rows that come first in the lock order.
    When an admin action caused it, each cancelled booking is written to the action log (RNF-07).
    """
    cancelled = []
    to_cancel = (
        bookings.filter(status__in=Booking.ACTIVE_STATUSES, start__gt=now())
        .select_for_update(of=("self",))
        .select_related("court")
        .order_by("pk")
    )
    for booking in to_cancel:
        before = booking_snapshot(booking)
        booking.status = Booking.Status.SYSTEM_CANCELLED
        booking.system_reason = reason
        booking.cancelled_by = None
        booking.cancelled_at = now()
        booking.save()
        if actor is not None:
            log_action(actor, "booking_system_cancelled", booking, before=before, after=booking_snapshot(booking))
        cancelled.append(booking)
    return cancelled
