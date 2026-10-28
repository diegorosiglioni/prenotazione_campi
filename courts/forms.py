from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from courts.models import Court, CourtType


class PriceForm(forms.Form):
    """New price of a court type, greater than zero (RF-05)."""

    court_type = forms.ModelChoiceField(queryset=CourtType.objects.all(), widget=forms.HiddenInput)
    price = forms.DecimalField(
        label=_("Prezzo (€)"), max_digits=6, decimal_places=2, min_value=Decimal("0.01"), localize=True
    )


class BlockForm(forms.Form):
    """A court block with date and time of start and end, also over several days (RF-14)."""

    court = forms.ModelChoiceField(label=_("Campo"), queryset=Court.objects.filter(is_active=True))
    start = forms.SplitDateTimeField(label=_("Inizio"), help_text=_("Data (gg/mm/aaaa) e ora (hh:mm)"))
    end = forms.SplitDateTimeField(label=_("Fine"), help_text=_("Data (gg/mm/aaaa) e ora (hh:mm)"))

    def clean(self):
        cleaned_data = super().clean()
        start, end = cleaned_data.get("start"), cleaned_data.get("end")
        if start and end and end <= start:
            raise ValidationError(_("La fine deve essere dopo l'inizio."))
        return cleaned_data
