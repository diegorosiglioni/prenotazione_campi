import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext

from accounts.views import member_required
from bookings.calendar import day_grid, visible_day
from bookings.forms import AdminBookingForm
from bookings.models import Booking
from bookings.services.booking import create_booking
from common.clock import now
from common.errors import DomainError
from courts.models import Court


def _parse_date(value):
    try:
        return datetime.date.fromisoformat(value or "")
    except ValueError:
        return None


@login_required
def calendar(request):
    """Day calendar (RF-11). With HTMX only the grid is sent back."""
    day = visible_day(_parse_date(request.GET.get("date")), request.user)
    courts, rows = day_grid(day, request.user)
    context = {
        "day": day,
        "previous_day": visible_day(day - datetime.timedelta(days=1), request.user),
        "next_day": visible_day(day + datetime.timedelta(days=1), request.user),
        "courts": courts,
        "rows": rows,
    }
    template = "bookings/_calendar.html" if request.headers.get("HX-Request") else "bookings/calendar.html"
    return render(request, template, context)


def _requested_slot(request):
    """Court and start from the query string, in Italian time; 404 if they make no sense."""
    court = get_object_or_404(Court.objects.select_related("court_type"), code=request.GET.get("court"), is_active=True)
    day = _parse_date(request.GET.get("date"))
    try:
        time = datetime.time.fromisoformat(request.GET.get("time") or "")
    except ValueError:
        time = None
    if day is None or time is None:
        raise Http404
    return court, timezone.make_aware(datetime.datetime.combine(day, time))


@login_required
def book(request):
    """Summary before confirming (RF-42); on confirmation, create the booking or show the broken rule (RF-43)."""
    court, start = _requested_slot(request)
    user = request.user
    form = AdminBookingForm(request.POST or None) if user.is_admin else None
    error = None

    if request.method == "POST" and (form is None or form.is_valid()):
        member = form.cleaned_data["member"] if form else user
        offered = form.cleaned_data["offered"] if form else False
        try:
            create_booking(user, member, court, start, offered=offered)
        except DomainError as domain_error:
            error = domain_error.message
        else:
            messages.success(request, gettext("Prenotazione confermata."))
            if user.is_admin:
                return redirect(f"{reverse('calendar')}?date={timezone.localtime(start).date().isoformat()}")
            return redirect("my_bookings")

    context = {
        "court": court,
        "start": start,
        "end": start + court.court_type.slot_length,
        "price": court.court_type.price,
        "form": form,
        "error": error,
    }
    return render(request, "bookings/confirm.html", context)


@member_required
def my_bookings(request):
    """The member's own bookings, upcoming and past, with status and price (RF-12, RF-20)."""
    bookings = Booking.objects.filter(member=request.user).select_related("court")
    current = now()
    context = {
        "upcoming": bookings.filter(end__gt=current).order_by("start"),
        "past": bookings.filter(end__lte=current).order_by("-start"),
    }
    return render(request, "bookings/my_bookings.html", context)
