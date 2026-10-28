import datetime
from zoneinfo import ZoneInfo

from django import forms
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.utils import translation

UTC = datetime.timezone.utc
ROME = ZoneInfo("Europe/Rome")
SAMPLE_DATE = datetime.date(2026, 3, 9)
SAMPLE_TIME = datetime.time(20, 30)
SAMPLE_DATETIME = datetime.datetime(2026, 3, 9, 20, 30, tzinfo=ROME)


def render(template_code, **context):
    return Template(template_code).render(Context(context)).strip()


class DayForm(forms.Form):
    day = forms.DateField()


class DateFormatTests(SimpleTestCase):
    def assert_dates_are_dd_mm_yyyy(self, language):
        with translation.override(language):
            self.assertEqual(render("{{ value }}", value=SAMPLE_DATE), "09/03/2026")
            self.assertEqual(render("{{ value|date }}", value=SAMPLE_DATE), "09/03/2026")
            self.assertEqual(
                render('{{ value|date:"SHORT_DATE_FORMAT" }}', value=SAMPLE_DATE), "09/03/2026"
            )

    def test_rnf10_date_format_it(self):
        self.assert_dates_are_dd_mm_yyyy("it")

    def test_rnf10_date_format_en(self):
        self.assert_dates_are_dd_mm_yyyy("en")

    def assert_times_are_24_hours(self, language):
        with translation.override(language):
            self.assertEqual(render("{{ value }}", value=SAMPLE_TIME), "20:30")
            self.assertEqual(render("{{ value|time }}", value=SAMPLE_TIME), "20:30")
            self.assertEqual(render("{{ value }}", value=SAMPLE_DATETIME), "09/03/2026 20:30")

    def test_rnf10_time_24_hours_it(self):
        self.assert_times_are_24_hours("it")

    def test_rnf10_time_24_hours_en(self):
        self.assert_times_are_24_hours("en")

    def test_rnf10_date_input_dd_mm_yyyy_en(self):
        # Django's default English input formats read 09/03/2026 as 3 September.
        for language in ("it", "en"):
            with self.subTest(language=language), translation.override(language):
                form = DayForm(data={"day": "09/03/2026"})
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data["day"], SAMPLE_DATE)


class TranslationTests(SimpleTestCase):
    def test_rnf02_base_template_translated(self):
        cases = {"it": "Prenotazione campi", "en": "Court booking"}
        for language, title in cases.items():
            with self.subTest(language=language), translation.override(language):
                html = render_to_string("base.html")
                self.assertIn(f"<title>{title}</title>", html)
                self.assertIn(f'<html lang="{language}">', html)


class TimeZoneDisplayTests(SimpleTestCase):
    def test_rnf03_display_in_rome_time_across_dst(self):
        # 2026 switches: Sunday 29 March (UTC+1 -> UTC+2) and Sunday 25 October (back to UTC+1).
        cases = [
            (datetime.datetime(2026, 3, 28, 7, 0, tzinfo=UTC), "28/03/2026 08:00"),
            (datetime.datetime(2026, 3, 29, 6, 0, tzinfo=UTC), "29/03/2026 08:00"),
            (datetime.datetime(2026, 10, 24, 6, 0, tzinfo=UTC), "24/10/2026 08:00"),
            (datetime.datetime(2026, 10, 25, 7, 0, tzinfo=UTC), "25/10/2026 08:00"),
        ]
        for language in ("it", "en"):
            for instant, expected in cases:
                with self.subTest(language=language, instant=instant), translation.override(language):
                    self.assertEqual(render("{{ value }}", value=instant), expected)
