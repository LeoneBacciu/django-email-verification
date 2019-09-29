from django.contrib.auth import get_user_model
from django.db import models


class User(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    email_token = models.CharField(max_length=100, null=True, default=None)
