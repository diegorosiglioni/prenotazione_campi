from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeBoundary, RangeOperators
from django.db import models
from django.db.models import F, Func, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.clock import now
from courts.models import Court


class TsTzRange(Func):
    """PostgreSQL tstzrange(start, end, '[)'): start included, end excluded."""

    function = "TSTZRANGE"
    output_field = DateTimeRangeField()


class BookingStatus(models.TextChoices):
    """The 8 states of RF-21."""

    BOOKED = "booked", _("Prenotata")
    PAID = "paid", _("Pagata")
    OFFERED = "offered", _("Offerta")
    CANCELLED = "cancelled", _("Cancellata")
    ADMIN_CANCELLED = "admin_cancelled", _("Cancellata dall'admin")
    SYSTEM_CANCELLED = "system_cancelled", _("Annullata dal sistema")
    NO_SHOW = "no_show", _("No-show")
    UNPAID = "unpaid", _("Non pagata")


# States that keep the court and the member busy (RF-07, RF-44).
OCCUPYING_STATUSES = [
    BookingStatus.BOOKED,
    BookingStatus.PAID,
    BookingStatus.OFFERED,
    BookingStatus.NO_SHOW,
    BookingStatus.UNPAID,
]

# States of an active booking, if it has not ended yet (RF-09).
ACTIVE_STATUSES = [BookingStatus.BOOKED, BookingStatus.PAID, BookingStatus.OFFERED]


class SystemReason(models.TextChoices):
    """Fixed reasons of system cancellations, translated when shown (RF-18)."""

    ACCOUNT_BLOCKED = "account_blocked", _("account bloccato")
    ACCOUNT_DEACTIVATED = "account_deactivated", _("account disattivato")
    COURT_BLOCKED = "court_blocked", _("campo bloccato")


class Booking(models.Model):
    """One slot of one court, held by one member (RF-03, RF-41)."""

    Status = BookingStatus
    OCCUPYING_STATUSES = OCCUPYING_STATUSES
    ACTIVE_STATUSES = ACTIVE_STATUSES

    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings")
    court = models.ForeignKey(Court, on_delete=models.PROTECT, related_name="bookings")
    start = models.DateTimeField(_("inizio"))
    end = models.DateTimeField(_("fine"))
    # Copied from the court type at creation: later price changes do not touch it (RF-05).
    price = models.DecimalField(_("prezzo"), max_digits=6, decimal_places=2)
    status = models.CharField(_("stato"), max_length=20, choices=BookingStatus.choices, default=BookingStatus.BOOKED)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(default=now)
    # Empty cancelled_by with a cancelled_at means a system cancellation (RF-20).
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    system_reason = models.CharField(max_length=30, choices=SystemReason.choices, blank=True)

    class Meta:
        ordering = ["start", "court"]
        constraints = [
            ExclusionConstraint(
                name="booking_no_court_overlap",
                expressions=[
                    (TsTzRange("start", "end", RangeBoundary()), RangeOperators.OVERLAPS),
                    ("court", RangeOperators.EQUAL),
                ],
                condition=Q(status__in=OCCUPYING_STATUSES),
            ),
            ExclusionConstraint(
                name="booking_no_member_overlap",
                expressions=[
                    (TsTzRange("start", "end", RangeBoundary()), RangeOperators.OVERLAPS),
                    ("member", RangeOperators.EQUAL),
                ],
                condition=Q(status__in=OCCUPYING_STATUSES),
            ),
            models.CheckConstraint(condition=Q(end__gt=F("start")), name="booking_end_after_start"),
            models.CheckConstraint(condition=Q(price__gte=0), name="booking_price_not_negative"),
        ]

    def __str__(self):
        return f"{self.court} {timezone.localtime(self.start):%d/%m/%Y %H:%M} ({self.member.card_code})"
