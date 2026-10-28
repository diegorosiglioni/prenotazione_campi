"""Admin actions on prices and court blocks (RF-05, RF-14). Each one writes the action log (RNF-07)."""

from django.db import transaction

from audit.services import log_action
from bookings.models import Booking, SystemReason
from bookings.services.booking import cancel_by_system
from common.clock import now
from common.errors import DomainError
from courts.models import Court, CourtBlock, CourtType


def block_snapshot(block):
    return {"court": block.court.code, "start": block.start, "end": block.end}


@transaction.atomic
def set_price(actor, court_type, price):
    """New price for every court of this type; existing bookings keep theirs (RF-05)."""
    court_type = CourtType.objects.select_for_update().get(pk=court_type.pk)
    before = {"price": court_type.price}
    court_type.price = price
    court_type.save()
    log_action(actor, "price_changed", court_type, before=before, after={"price": court_type.price})
    return court_type


@transaction.atomic
def block_court(actor, court, start, end):
    """Make the court unbookable from `start` to `end` and cancel the bookings not started yet (RF-14)."""
    # Same lock as create_booking: a booking and a block on this court cannot cross (RNF-04).
    court = Court.objects.select_for_update().get(pk=court.pk)
    if start <= now():
        raise DomainError("slot_in_past")
    block = CourtBlock.objects.create(court=court, start=start, end=end)
    log_action(actor, "court_blocked", block, after=block_snapshot(block))
    overlapping = Booking.objects.filter(court=court, start__lt=end, end__gt=start)
    cancel_by_system(overlapping, SystemReason.COURT_BLOCKED, actor)
    return block


@transaction.atomic
def remove_block(actor, block):
    """The court is bookable again; cancelled bookings stay cancelled (RF-14)."""
    Court.objects.select_for_update().get(pk=block.court_id)
    block = CourtBlock.objects.select_related("court").get(pk=block.pk)
    log_action(actor, "court_block_removed", block, before=block_snapshot(block))
    block.delete()
