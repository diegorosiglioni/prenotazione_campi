from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext

from accounts.views import admin_required
from common.clock import now
from common.errors import DomainError
from courts import services
from courts.forms import BlockForm, PriceForm
from courts.models import CourtBlock, CourtType


@admin_required
def staff_courts(request):
    """Prices per court type (RF-05) and court blocks (RF-14)."""
    court_types = list(CourtType.objects.all())
    block_form = BlockForm()
    price_forms = {
        court_type.pk: PriceForm(initial={"court_type": court_type, "price": court_type.price})
        for court_type in court_types
    }

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "price":
            form = PriceForm(request.POST)
            if form.is_valid():
                services.set_price(request.user, form.cleaned_data["court_type"], form.cleaned_data["price"])
                messages.success(request, gettext("Prezzo aggiornato."))
                return redirect("staff_courts")
            court_type_pk = form.data.get("court_type")
            if court_type_pk and court_type_pk.isdigit() and int(court_type_pk) in price_forms:
                price_forms[int(court_type_pk)] = form
        elif action == "block":
            block_form = BlockForm(request.POST)
            if block_form.is_valid():
                data = block_form.cleaned_data
                try:
                    services.block_court(request.user, data["court"], data["start"], data["end"])
                except DomainError as error:
                    block_form.add_error(None, error.message)
                else:
                    messages.success(request, gettext("Campo bloccato."))
                    return redirect("staff_courts")
        elif action == "remove":
            block = get_object_or_404(CourtBlock, pk=request.POST.get("block"))
            services.remove_block(request.user, block)
            messages.success(request, gettext("Blocco rimosso."))
            return redirect("staff_courts")
        else:
            return HttpResponseBadRequest()

    blocks = CourtBlock.objects.filter(end__gt=now()).select_related("court")
    context = {
        "prices": [(court_type, price_forms[court_type.pk]) for court_type in court_types],
        "blocks": blocks,
        "block_form": block_form,
    }
    return render(request, "courts/staff/courts.html", context)
