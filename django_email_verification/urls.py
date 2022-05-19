from django.urls import path

from .views import verify_email_page, verify_password_page

urlpatterns = [
    path('email/<str:token>', verify_email_page),
    path('password/<str:token>', verify_password_page)
]
