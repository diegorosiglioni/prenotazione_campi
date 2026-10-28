"""Django settings. Every machine-specific or secret value comes from the environment."""

from pathlib import Path

from dotenv import load_dotenv

from config.env import env_bool, env_list, env_str

BASE_DIR = Path(__file__).resolve().parent.parent

# On the PC the values live in .env; in CI and production they are real environment
# variables, which load_dotenv never overrides.
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = env_str("DJANGO_SECRET_KEY")
DEBUG = env_bool("DJANGO_DEBUG")
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")


# django.contrib.admin is left out on purpose: it would let data be edited without the
# service rules (RF-45) and without the action log (RNF-07).
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "common",
    "accounts",
    "courts",
    "bookings",
    "notifications",
    "audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database: PostgreSQL only, also for tests (exclusion constraints, RNF-04).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env_str("POSTGRES_DB"),
        "USER": env_str("POSTGRES_USER"),
        "PASSWORD": env_str("POSTGRES_PASSWORD"),
        # 127.0.0.1, not localhost: on Windows localhost tries IPv6 first and can hang.
        "HOST": env_str("POSTGRES_HOST", "127.0.0.1"),
        "PORT": env_str("POSTGRES_PORT", "5432"),
        # Fail with a clear error instead of waiting forever for an unreachable server.
        "OPTIONS": {"connect_timeout": 10},
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization (RNF-02, RNF-03, RNF-10).
# Source strings are Italian; locale/en holds the English translation.
LANGUAGE_CODE = "it"
LANGUAGES = [
    ("it", "Italiano"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
# Dates as dd/mm/yyyy and 24-hour times in both languages.
FORMAT_MODULE_PATH = ["config.formats"]
USE_I18N = True
# Instants are stored in UTC and shown in Italian time, daylight saving included.
TIME_ZONE = "Europe/Rome"
USE_TZ = True


# Static files
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
