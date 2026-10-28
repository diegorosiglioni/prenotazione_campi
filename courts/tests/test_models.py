import datetime
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from courts.models import Court, CourtBlock, CourtType

T0 = datetime.datetime(2026, 7, 10, 8, 0, tzinfo=datetime.timezone.utc)


class CourtDataTests(TestCase):
    def test_rf03_courts_created_by_migration(self):
        types = {t.code: (t.slot_minutes, t.price) for t in CourtType.objects.all()}
        self.assertEqual(
            types,
            {
                "football": (90, Decimal("60.00")),
                "tennis": (60, Decimal("18.00")),
                "basketball": (60, Decimal("25.00")),
                "bocce": (60, Decimal("10.00")),
            },
        )
        courts = {c.code: c.court_type.code for c in Court.objects.select_related("court_type")}
        self.assertEqual(
            courts,
            {
                "football": "football",
                "tennis_1": "tennis",
                "tennis_2": "tennis",
                "basketball": "basketball",
                "bocce": "bocce",
            },
        )
        self.assertTrue(all(c.is_active for c in Court.objects.all()))

    def test_rf06_tennis_courts_have_distinct_names(self):
        names = {str(Court.objects.get(code="tennis_1")), str(Court.objects.get(code="tennis_2"))}
        self.assertEqual(len(names), 2)

    def test_rf05_price_positive_in_db(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            CourtType.objects.filter(code="tennis").update(price=Decimal("0"))

    def test_rf03_slot_minutes_positive_in_db(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            CourtType.objects.filter(code="tennis").update(slot_minutes=0)

    def test_rf14_block_end_after_start_in_db(self):
        court = Court.objects.get(code="bocce")
        with self.assertRaises(IntegrityError), transaction.atomic():
            CourtBlock.objects.create(court=court, start=T0, end=T0)
