from getpass import getpass

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.utils.translation import gettext as _

from accounts.models import User, normalize_card_code


class Command(BaseCommand):
    help = "Create the single admin account (RF-01). The password is asked twice and never shown."

    def add_arguments(self, parser):
        parser.add_argument("--card-code", help="Reserved card code of the admin, e.g. ADMIN")
        parser.add_argument("--first-name")
        parser.add_argument("--last-name")

    def handle(self, *args, card_code=None, first_name=None, last_name=None, **options):
        if User.objects.filter(role=User.Role.ADMIN).exists():
            raise CommandError(_("L'admin esiste già. Per una nuova password usare: changepassword <codice>."))

        admin = User(
            card_code=normalize_card_code(card_code or input(_("Codice riservato dell'admin: "))),
            first_name=(first_name or input(_("Nome: "))).strip(),
            last_name=(last_name or input(_("Cognome: "))).strip(),
            role=User.Role.ADMIN,
        )
        password = getpass(_("Password: "))
        if password != getpass(_("Ripeti la password: ")):
            raise CommandError(_("Le due password non coincidono."))
        try:
            password_validation.validate_password(password, admin)
            # Card code format and uniqueness, single admin (RF-01, RF-31).
            admin.full_clean(exclude=["password"])
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from error

        try:
            with transaction.atomic():
                admin = User.objects.create_admin(
                    admin.card_code, password, first_name=admin.first_name, last_name=admin.last_name
                )
        except IntegrityError as error:
            # Another admin was created in the meantime: the database refuses a second one.
            raise CommandError(_("L'admin esiste già.")) from error
        self.stdout.write(self.style.SUCCESS(_("Admin creato con il codice %(code)s.") % {"code": admin.card_code}))
