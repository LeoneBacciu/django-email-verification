from django.urls import path, include

from django_email_verification import urls, verify_email_view

urlpatterns = [
    path('confirm/', include(urls)),
    path('confirm/', verify_email_view(lambda request: None)),
]
