from django.urls import path

from django_email_verification import verify_email_view

urlpatterns = [
    path('confirm/', verify_email_view(lambda request, token: None)),
]
