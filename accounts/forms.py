from django import forms
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth import forms as auth_forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from accounts.models import User, normalize_card_code
from accounts.services import clear_failed_logins, is_login_locked, record_failed_login


class LoginForm(auth_forms.AuthenticationForm):
    """Card code and password (RF-31), with the lock after 5 failed logins (RNF-05)."""

    # One message for wrong password, unknown code and deactivated account:
    # nobody learns which card codes exist.
    error_messages = {
        "invalid_login": _("Codice tessera o password non corretti."),
        "locked": _("Troppi tentativi falliti: riprova tra 15 minuti."),
    }

    def clean(self):
        card_code = normalize_card_code(self.cleaned_data.get("username"))
        password = self.cleaned_data.get("password")
        if card_code and password:
            if is_login_locked(card_code):
                raise ValidationError(self.error_messages["locked"], code="locked")
            # Django's backend refuses deactivated accounts (RF-40).
            self.user_cache = authenticate(self.request, username=card_code, password=password)
            if self.user_cache is None:
                record_failed_login(card_code)
                raise ValidationError(self.error_messages["invalid_login"], code="invalid_login")
            clear_failed_logins(card_code)
        return self.cleaned_data


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    """Changing the password also ends the obligation to change it (RF-32)."""

    def save(self, commit=True):
        self.user.must_change_password = False
        return super().save(commit)


class LanguageForm(forms.ModelForm):
    """The only personal data a member can change, besides the password (RF-55)."""

    class Meta:
        model = User
        fields = ["language"]


class TemporaryPasswordForm(forms.Form):
    """A temporary password typed by the admin (RF-32, RF-33), at least 8 characters (RNF-05)."""

    password1 = forms.CharField(
        label=_("Password temporanea"), strip=False, widget=forms.PasswordInput(render_value=False)
    )
    password2 = forms.CharField(
        label=_("Ripeti la password temporanea"), strip=False, widget=forms.PasswordInput(render_value=False)
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2:
            if password1 != password2:
                self.add_error("password2", _("Le due password non coincidono."))
            else:
                try:
                    password_validation.validate_password(password1)
                except ValidationError as error:
                    self.add_error("password1", error)
        return cleaned_data


class MemberForm(forms.ModelForm):
    """Member data edited by the admin (RF-30, RF-35). Email and phone are optional."""

    class Meta:
        model = User
        fields = ["card_code", "first_name", "last_name", "card_expiry", "email", "phone"]
        widgets = {"card_expiry": forms.DateInput(attrs={"placeholder": _("gg/mm/aaaa")})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional in the model only because the admin has no card (RF-31).
        self.fields["card_expiry"].required = True

    def clean_card_code(self):
        return normalize_card_code(self.cleaned_data["card_code"])


class MemberCreateForm(TemporaryPasswordForm, MemberForm):
    """A new member: data, language and temporary password (RF-30, RF-32)."""

    class Meta(MemberForm.Meta):
        fields = MemberForm.Meta.fields + ["language"]
