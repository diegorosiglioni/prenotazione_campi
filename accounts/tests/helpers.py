import datetime

from accounts.models import User

PASSWORD = "password-1234"
CARD_EXPIRY = datetime.date(2027, 12, 31)


def make_member(card_code="ABC1", password=PASSWORD, **fields):
    fields.setdefault("first_name", "Mario")
    fields.setdefault("last_name", "Rossi")
    fields.setdefault("card_expiry", CARD_EXPIRY)
    return User.objects.create_member(card_code=card_code, password=password, **fields)


def make_admin(card_code="ADMIN", password=PASSWORD):
    return User.objects.create_admin(
        card_code=card_code, first_name="Gestore", last_name="Campi", password=password
    )
