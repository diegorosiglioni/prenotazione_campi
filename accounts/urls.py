from django.contrib.auth import views as auth_views
from django.urls import path

from accounts import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password/", views.PasswordChangeView.as_view(), name="password_change"),
    path("account/", views.account, name="account"),
    path("staff/users/", views.staff_user_list, name="staff_users"),
    path("staff/users/new/", views.staff_user_create, name="staff_user_create"),
    path("staff/users/<int:pk>/", views.staff_user_detail, name="staff_user_detail"),
]
