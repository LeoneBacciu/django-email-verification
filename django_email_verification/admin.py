from django.contrib import admin
from django.conf import settings

from .models import User

try:
    if settings.EMAIL_MODEL_ADMIN:
        admin.site.register(User)
except AttributeError:
    pass
