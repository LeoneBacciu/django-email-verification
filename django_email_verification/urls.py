from .views import verify
from django.urls import path

urlpatterns = [
    path('<str:token>', verify)
]
