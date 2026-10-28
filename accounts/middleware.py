from django.conf import settings
from django.shortcuts import redirect
from django.utils import translation


class UserLanguageMiddleware:
    """Pick the language of each request (RNF-02).

    After login: the user's own language. Before login: the one chosen with the selector
    on the login page (a cookie), otherwise Italian. The browser's language is ignored.
    Must come after AuthenticationMiddleware and before MessageMiddleware, so messages
    are stored in the same language.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = self.language_for(request)
        with translation.override(language):
            request.LANGUAGE_CODE = language
            response = self.get_response(request)
        response.headers.setdefault("Content-Language", language)
        return response

    @staticmethod
    def language_for(request):
        if request.user.is_authenticated:
            return request.user.language
        chosen = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        if chosen in dict(settings.LANGUAGES):
            return chosen
        return settings.LANGUAGE_CODE


class PasswordChangeRequiredMiddleware:
    """Send users with a temporary password to the password change page (RF-32)."""

    ALLOWED_VIEWS = {"password_change", "logout", "set_language"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = request.user
        if (
            user.is_authenticated
            and user.must_change_password
            and request.resolver_match.url_name not in self.ALLOWED_VIEWS
        ):
            return redirect("password_change")
        return None
