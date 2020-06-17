from django.conf import settings
from django.shortcuts import render

from .Confirm import verifyToken
from .errors import NotAllFieldCompiled


def verify(request, email, email_token):
    try:
        template = settings.EMAIL_PAGE_TEMPLATE
        return render(request, template, {'success': verifyToken(email, email_token)})
    except AttributeError:
        raise NotAllFieldCompiled('EMAIL_PAGE_TEMPLATE field not found')

