from django.urls import path, include

from django_email_verification import urls, verify_view

urlpatterns = [
    path('email/', include(urls)),
    path('confirm/<str:token>/', verify_view(lambda request, token: None)),
    path('named_view/', lambda request: None, name='named_view_name'),
]
