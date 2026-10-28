"""Main URL configuration. Django's admin site is not exposed (see settings.INSTALLED_APPS)."""

from django.urls import include, path

urlpatterns = [
    # set_language: the language selector on the login page (RNF-02).
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include("accounts.urls")),
]
