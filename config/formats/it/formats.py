"""Date and time formats (RNF-10): dd/mm/yyyy and 24-hour times.

Names not defined here fall back to Django's own Italian formats.
"""

DATE_FORMAT = "d/m/Y"
SHORT_DATE_FORMAT = "d/m/Y"
TIME_FORMAT = "H:i"
DATETIME_FORMAT = "d/m/Y H:i"
SHORT_DATETIME_FORMAT = "d/m/Y H:i"

DATE_INPUT_FORMATS = [
    "%d/%m/%Y",
    "%Y-%m-%d",  # ISO, sent by <input type="date">
]
TIME_INPUT_FORMATS = ["%H:%M"]
DATETIME_INPUT_FORMATS = ["%d/%m/%Y %H:%M"]
