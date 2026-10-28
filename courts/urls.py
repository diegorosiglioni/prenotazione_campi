from django.urls import path

from courts import views

urlpatterns = [
    path("staff/courts/", views.staff_courts, name="staff_courts"),
]
