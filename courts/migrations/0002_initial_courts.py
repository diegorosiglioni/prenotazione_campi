"""Create the 4 court types and the 5 courts of the requirements (RF-03, RF-06)."""

from decimal import Decimal

from django.db import migrations

COURT_TYPES = [
    # code, slot minutes, price in euro
    ("football", 90, Decimal("60.00")),
    ("tennis", 60, Decimal("18.00")),
    ("basketball", 60, Decimal("25.00")),
    ("bocce", 60, Decimal("10.00")),
]

COURTS = [
    # code, court type code
    ("football", "football"),
    ("tennis_1", "tennis"),
    ("tennis_2", "tennis"),
    ("basketball", "basketball"),
    ("bocce", "bocce"),
]


def create_courts(apps, schema_editor):
    CourtType = apps.get_model("courts", "CourtType")
    Court = apps.get_model("courts", "Court")
    types = {}
    for code, slot_minutes, price in COURT_TYPES:
        types[code] = CourtType.objects.create(code=code, slot_minutes=slot_minutes, price=price)
    for code, type_code in COURTS:
        Court.objects.create(code=code, court_type=types[type_code])


def delete_courts(apps, schema_editor):
    apps.get_model("courts", "Court").objects.all().delete()
    apps.get_model("courts", "CourtType").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("courts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_courts, delete_courts),
    ]
