from .Confirm import verify
from django.urls import path

urlpatterns = [
    path('<str:email_token>', verify)
]
