from django.urls import path

from bookings import views

urlpatterns = [
    path("calendar/", views.calendar, name="calendar"),
    path("book/", views.book, name="book"),
    path("bookings/", views.my_bookings, name="my_bookings"),
]
