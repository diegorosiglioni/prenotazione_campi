"""Domain errors: a broken rule, identified by a code (specifiche-tecniche, section 3)."""

from django.utils.translation import gettext_lazy as _

MESSAGES = {
    "out_of_hours": _("Orario non valido: si gioca dalle 8:00 alle 23:00, con inizio ogni 15 minuti."),
    "slot_in_past": _("Questo orario è già passato."),
    "out_of_window": _("Si può prenotare al massimo fino a 14 giorni da oggi."),
    "slot_taken": _("Il campo è già occupato in questo orario."),
    "member_overlap": _("Il tesserato ha già una prenotazione in questo orario, anche su un altro campo."),
    "court_blocked": _("Il campo non è disponibile in questo orario."),
    "limit_reached": _("Hai già 3 prenotazioni attive: è il massimo consentito."),
    "card_expired": _("La tessera è scaduta: dopo il rinnovo potrai prenotare."),
    "card_expires_before_slot": _("La tessera scade prima della data di questo slot."),
    "account_blocked": _("L'account è bloccato: rivolgiti all'admin."),
    "account_inactive": _("L'account è disattivato."),
    "not_a_member": _("La prenotazione deve essere intestata a un tesserato."),
}


class DomainError(Exception):
    """Raised by services when a rule is broken. Views show `message` in the user's language."""

    def __init__(self, code):
        if code not in MESSAGES:
            raise ValueError(f"Unknown domain error code: {code}")
        super().__init__(code)
        self.code = code

    @property
    def message(self):
        return str(MESSAGES[self.code])
