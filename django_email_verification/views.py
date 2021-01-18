from django.conf import settings
from django.shortcuts import render

from .confirm import verify_token
from .errors import NotAllFieldCompiled


def verify(request, email, email_token):
    try:
        template = settings.EMAIL_PAGE_TEMPLATE
        return render(request, template, {'success': verify_token(email, email_token)})
    except AttributeError:
        raise NotAllFieldCompiled('EMAIL_PAGE_TEMPLATE field not found')

