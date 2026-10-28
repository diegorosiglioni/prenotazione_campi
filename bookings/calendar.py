"""The day grid of the calendar (RF-11): one column per court, one row every 15 minutes."""

import datetime
from dataclasses import dataclass
from urllib.parse import urlencode

from django.urls import reverse
from django.utils import timezone

from bookings.models import Booking
from bookings.services.booking import CLOSING_TIME, OPENING_TIME, STEP_MINUTES, last_bookable_date, today
from common.clock import now
from courts.models import Court, CourtBlock

STEP = datetime.timedelta(minutes=STEP_MINUTES)


@dataclass
class Cell:
    state: str  # "free", "booked", "blocked" or "past"
    booking: Booking | None = None
    first: bool = False  # first row of the booking
    own: bool = False  # the booking belongs to the viewer
    url: str = ""  # link to the summary, when a whole slot can start here


def visible_day(day, viewer):
    """Members see from today to the last bookable day (RF-08); the admin sees any day."""
    if day is None:
        return today()
    if viewer.is_admin:
        return day
    return min(max(day, today()), last_bookable_date())


def day_grid(day, viewer):
    """Return the active courts and the rows of `day`; each row has a time and one cell per court."""
    courts = list(Court.objects.filter(is_active=True).select_related("court_type"))
    opening = timezone.make_aware(datetime.datetime.combine(day, OPENING_TIME))
    closing = timezone.make_aware(datetime.datetime.combine(day, CLOSING_TIME))
    bookings = Booking.objects.filter(
        court__in=courts, status__in=Booking.OCCUPYING_STATUSES, start__lt=closing, end__gt=opening
    ).select_related("member")
    blocks = CourtBlock.objects.filter(court__in=courts, start__lt=closing, end__gt=opening)
    bookings_by_court = {court.pk: [] for court in courts}
    blocks_by_court = {court.pk: [] for court in courts}
    for booking in bookings:
        bookings_by_court[booking.court_id].append(booking)
    for block in blocks:
        blocks_by_court[block.court_id].append(block)

    can_link = viewer.is_admin or day <= last_bookable_date()
    current = now()
    rows = []
    time = opening
    while time < closing:
        cells = [
            _cell(court, time, closing, current, viewer, can_link, bookings_by_court[court.pk], blocks_by_court[court.pk])
            for court in courts
        ]
        rows.append({"time": time, "cells": cells})
        time += STEP
    return courts, rows


def _overlaps(items, start, end):
    return any(item.start < end and item.end > start for item in items)


def _cell(court, time, closing, current, viewer, can_link, bookings, blocks):
    for booking in bookings:
        if booking.start <= time < booking.end:
            return Cell("booked", booking, first=booking.start == time, own=booking.member_id == viewer.pk)
    if _overlaps(blocks, time, time + STEP):
        return Cell("blocked")
    if time <= current:
        return Cell("past")
    end = time + court.court_type.slot_length
    fits = end <= closing and not _overlaps(bookings, time, end) and not _overlaps(blocks, time, end)
    if not (fits and can_link):
        return Cell("free")
    query = urlencode({"court": court.code, "date": time.date().isoformat(), "time": time.strftime("%H:%M")})
    return Cell("free", url=f"{reverse('book')}?{query}")
