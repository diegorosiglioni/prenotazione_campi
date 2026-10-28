from functools import wraps

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import translation
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from accounts import services
from accounts.forms import (
    LanguageForm,
    LoginForm,
    MemberCreateForm,
    MemberForm,
    PasswordChangeForm,
    TemporaryPasswordForm,
)
from accounts.models import User


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class PasswordChangeView(SuccessMessageMixin, auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = PasswordChangeForm
    success_url = reverse_lazy("home")
    success_message = _("Password cambiata.")


@login_required
def home(request):
    # Until the calendar exists (piece 3): admin to the user list, members to their account.
    if request.user.is_admin:
        return redirect("staff_users")
    return redirect("account")


@login_required
def account(request):
    form = LanguageForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        # Confirm in the language just chosen.
        translation.activate(request.user.language)
        messages.success(request, gettext("Lingua aggiornata."))
        return redirect("account")
    return render(request, "accounts/account.html", {"form": form})


def admin_required(view):
    """Admin pages: anonymous users go to the login page, members get 403 (RF-01)."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return login_required(wrapper)


@admin_required
def staff_user_list(request):
    members = User.objects.filter(role=User.Role.MEMBER).order_by("last_name", "first_name", "card_code")
    return render(request, "accounts/staff/user_list.html", {"members": members})


@admin_required
def staff_user_create(request):
    form = MemberCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = {field: form.cleaned_data[field] for field in MemberCreateForm.Meta.fields}
        member = services.create_member(request.user, data, form.cleaned_data["password1"])
        messages.success(request, gettext("Account creato."))
        return redirect("staff_user_detail", pk=member.pk)
    return render(request, "accounts/staff/user_create.html", {"form": form})


@admin_required
def staff_user_detail(request, pk):
    member = get_object_or_404(User, pk=pk, role=User.Role.MEMBER)
    # The form gets its own copy: an invalid form must not change the data shown on the page.
    member_form = MemberForm(instance=User.objects.get(pk=pk))
    password_form = TemporaryPasswordForm()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update":
            member_form = MemberForm(request.POST, instance=User.objects.get(pk=pk))
            if member_form.is_valid():
                services.update_member(request.user, member, member_form.cleaned_data)
                messages.success(request, gettext("Dati aggiornati."))
                return redirect("staff_user_detail", pk=pk)
        elif action == "password":
            password_form = TemporaryPasswordForm(request.POST)
            if password_form.is_valid():
                services.set_temporary_password(request.user, member, password_form.cleaned_data["password1"])
                messages.success(request, gettext("Password temporanea assegnata."))
                return redirect("staff_user_detail", pk=pk)
        elif action == "deactivate":
            services.deactivate_member(request.user, member)
            messages.success(request, gettext("Account disattivato."))
            return redirect("staff_user_detail", pk=pk)
        elif action == "reactivate":
            services.reactivate_member(request.user, member)
            messages.success(request, gettext("Account riattivato."))
            return redirect("staff_user_detail", pk=pk)
        else:
            return HttpResponseBadRequest()

    context = {"member": member, "member_form": member_form, "password_form": password_form}
    return render(request, "accounts/staff/user_detail.html", context)
