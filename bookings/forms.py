from django import forms
from django.utils.translation import gettext_lazy as _

from accounts.models import User


class MemberChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.last_name} {obj.first_name} ({obj.card_code})"


class AdminBookingForm(forms.Form):
    """The admin books on behalf of an active member, possibly as an offered booking (RF-23, RF-40, RF-41)."""

    member = MemberChoiceField(
        label=_("Tesserato"),
        queryset=User.objects.filter(role=User.Role.MEMBER, is_active=True).order_by(
            "last_name", "first_name", "card_code"
        ),
    )
    offered = forms.BooleanField(label=_("Offerta (gratuita)"), required=False)
