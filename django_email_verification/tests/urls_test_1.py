from django.urls import path, include

from django_email_verification import urls, verify_email_view

urlpatterns = [
    path('confirm/', include(urls)),
    path('confirm/<str:token>/', verify_email_view(lambda request, token: None)),
    path('named_view/', lambda request: None, name='named_view_name'),
]
