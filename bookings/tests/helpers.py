import datetime
from zoneinfo import ZoneInfo

from bookings.models import Booking
from courts.models import Court

ROME = ZoneInfo("Europe/Rome")


def rome(year, month, day, hour=0, minute=0):
    """An instant given in Italian time."""
    return datetime.datetime(year, month, day, hour, minute, tzinfo=ROME)


def court(code):
    return Court.objects.select_related("court_type").get(code=code)


def insert_booking(member, court_code, start, status=Booking.Status.BOOKED, **fields):
    """Insert a booking directly, without the service rules (for setup and database tests)."""
    target = court(court_code)
    fields.setdefault("created_by", member)
    fields.setdefault("price", target.court_type.price)
    return Booking.objects.create(
        member=member,
        court=target,
        start=start,
        end=start + target.court_type.slot_length,
        status=status,
        **fields,
    )
