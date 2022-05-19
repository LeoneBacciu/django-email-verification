from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render

from .confirm import verify_email_view, verify_email, verify_password_view, verify_password
from .errors import NotAllFieldCompiled


@verify_email_view
def verify(request: WSGIRequest, token):
    try:
        template = settings.EMAIL_PAGE_TEMPLATE
        if not isinstance(template, str):
            raise AttributeError
        success, user = verify_email(token)
        return render(request, template, {'success': success, 'user': user, 'request': request})
    except AttributeError:
        raise NotAllFieldCompiled('EMAIL_PAGE_TEMPLATE field not found')


verify_email_page = verify


@verify_password_view
def verify_password_page(request: WSGIRequest, token):
    try:
        if request.method == 'POST' and (pwd := request.POST.get('password')) is not None:
            success, user = verify_password(token, pwd)
            return render(request, settings.EMAIL_PASSWORD_CHANGED_TEMPLATE,
                          {'success': success, 'user': user, 'request': request})
        return render(request, settings.EMAIL_PASSWORD_TEMPLATE, {'token': token})
    except AttributeError:
        raise NotAllFieldCompiled('EMAIL_PASSWORD templates field not found')
