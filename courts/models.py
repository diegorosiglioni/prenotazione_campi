import datetime

from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CourtType(models.Model):
    """Slot length and price are per court type: both tennis courts share them (RF-03, RF-05)."""

    class Code(models.TextChoices):
        FOOTBALL = "football", _("Calcio")
        TENNIS = "tennis", _("Tennis")
        BASKETBALL = "basketball", _("Pallacanestro")
        BOCCE = "bocce", _("Bocce")

    code = models.CharField(max_length=20, choices=Code.choices, unique=True)
    slot_minutes = models.PositiveSmallIntegerField(_("durata dello slot (minuti)"))
    price = models.DecimalField(_("prezzo"), max_digits=6, decimal_places=2)

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(condition=Q(slot_minutes__gt=0), name="court_type_slot_minutes_positive"),
            models.CheckConstraint(condition=Q(price__gt=0), name="court_type_price_positive"),
        ]

    def __str__(self):
        return str(self.get_code_display())

    @property
    def slot_length(self):
        return datetime.timedelta(minutes=self.slot_minutes)


class Court(models.Model):
    """One of the 5 courts, created by a data migration. Names come from the code via gettext."""

    class Code(models.TextChoices):
        FOOTBALL = "football", _("Calcio")
        TENNIS_1 = "tennis_1", _("Tennis 1")
        TENNIS_2 = "tennis_2", _("Tennis 2")
        BASKETBALL = "basketball", _("Pallacanestro")
        BOCCE = "bocce", _("Bocce")

    code = models.CharField(max_length=20, choices=Code.choices, unique=True)
    court_type = models.ForeignKey(CourtType, on_delete=models.PROTECT, related_name="courts")
    # No page changes it: an inactive court is hidden and cannot be booked (decisioni.md).
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return str(self.get_code_display())


class CourtBlock(models.Model):
    """A future interval in which the court cannot be booked (RF-14)."""

    court = models.ForeignKey(Court, on_delete=models.PROTECT, related_name="blocks")
    start = models.DateTimeField(_("inizio"))
    end = models.DateTimeField(_("fine"))

    class Meta:
        ordering = ["start"]
        constraints = [
            models.CheckConstraint(condition=Q(end__gt=F("start")), name="court_block_end_after_start"),
        ]

    def __str__(self):
        start, end = timezone.localtime(self.start), timezone.localtime(self.end)
        return f"{self.court} {start:%d/%m/%Y %H:%M}–{end:%d/%m/%Y %H:%M}"
