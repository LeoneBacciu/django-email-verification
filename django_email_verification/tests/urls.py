from django.urls import path, include

from django_email_verification import urls

urlpatterns = [
    path('email/', include(urls), name='email-endpoint'),
]
