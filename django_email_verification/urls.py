from .views import verify
from django.urls import path

urlpatterns = [
    path('<str:email>/<str:email_token>', verify)
]
