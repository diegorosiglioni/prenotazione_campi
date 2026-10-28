"""English uses the same formats as Italian (RNF-10), not Django's American ones."""

from config.formats.it.formats import (  # noqa: F401
    DATE_FORMAT,
    DATE_INPUT_FORMATS,
    DATETIME_FORMAT,
    DATETIME_INPUT_FORMATS,
    SHORT_DATE_FORMAT,
    SHORT_DATETIME_FORMAT,
    TIME_FORMAT,
    TIME_INPUT_FORMATS,
)
