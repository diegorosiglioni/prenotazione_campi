from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from common.clock import now

# Letters A-Z and digits only, stored uppercase (RF-31). The same pattern is a database constraint.
CARD_CODE_PATTERN = r"^[A-Z0-9]{1,20}$"

card_code_validator = RegexValidator(
    CARD_CODE_PATTERN,
    _("Il codice tessera può contenere solo lettere dalla A alla Z e numeri, fino a 20 caratteri."),
)


def normalize_card_code(value):
    """Card codes ignore case (RF-31): they are always stored and looked up in uppercase."""
    return (value or "").strip().upper()


class UserManager(BaseUserManager):
    def get_by_natural_key(self, card_code):
        return self.get(card_code=normalize_card_code(card_code))

    def create_member(self, card_code, password, **fields):
        # A temporary password must be changed at first login (RF-32).
        fields.setdefault("must_change_password", True)
        return self._create(card_code, password, role=User.Role.MEMBER, **fields)

    def create_admin(self, card_code, password, **fields):
        return self._create(card_code, password, role=User.Role.ADMIN, **fields)

    def _create(self, card_code, password, **fields):
        user = self.model(card_code=normalize_card_code(card_code), **fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """A member or the single admin (RF-01). Django's groups and permissions are not used."""

    class Role(models.TextChoices):
        MEMBER = "member", _("Tesserato")
        ADMIN = "admin", _("Admin")

    card_code = models.CharField(
        _("codice tessera"),
        max_length=20,
        unique=True,
        validators=[card_code_validator],
        error_messages={"unique": _("Questo codice tessera è già in uso.")},
    )
    first_name = models.CharField(_("nome"), max_length=100)
    last_name = models.CharField(_("cognome"), max_length=100)
    card_expiry = models.DateField(_("scadenza tessera"), null=True, blank=True)
    role = models.CharField(_("ruolo"), max_length=10, choices=Role.choices, default=Role.MEMBER)
    language = models.CharField(
        _("lingua"), max_length=2, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE
    )
    # False = deactivated account (RF-40); Django's login refuses inactive users.
    is_active = models.BooleanField(_("attivo"), default=True)
    # True from the second strike until the admin unblocks the account (RF-28, RF-29).
    is_blocked = models.BooleanField(_("bloccato"), default=False)
    must_change_password = models.BooleanField(_("deve cambiare la password"), default=False)
    email = models.EmailField(_("email"), blank=True)
    phone = models.CharField(_("telefono"), max_length=30, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "card_code"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("utente")
        verbose_name_plural = _("utenti")
        constraints = [
            models.CheckConstraint(
                condition=Q(card_code__regex=CARD_CODE_PATTERN),
                name="user_card_code_format",
                violation_error_message=card_code_validator.message,
            ),
            models.UniqueConstraint(
                fields=["role"],
                condition=Q(role="admin"),
                name="user_single_admin",
                violation_error_message=_("Esiste già un admin."),
            ),
            # Members need a card expiry date; the admin has none (RF-30, RF-31).
            models.CheckConstraint(
                condition=Q(role="member", card_expiry__isnull=False)
                | Q(role="admin", card_expiry__isnull=True),
                name="user_card_expiry_by_role",
                violation_error_message=_("La scadenza della tessera è obbligatoria per i tesserati."),
            ),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.card_code})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN


class LoginAttempt(models.Model):
    """A failed login for a card code, existing or not (RNF-05)."""

    card_code = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=now)

    class Meta:
        indexes = [models.Index(fields=["card_code", "created_at"])]
