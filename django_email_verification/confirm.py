import functools
import logging
from threading import Thread
from typing import Callable

import deprecation
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.template.loader import render_to_string
from django.urls import get_resolver
from django.utils import timezone

from .errors import InvalidUserModel, NotAllFieldCompiled
from .token import default_token_generator

logger = logging.getLogger('django_email_verification')
DJANGO_EMAIL_VERIFICATION_MORE_VIEWS_ERROR = 'ERROR: more than one verify view found'
DJANGO_EMAIL_VERIFICATION_NO_VIEWS_INFO = 'INFO: no verify view found'
DJANGO_EMAIL_VERIFICATION_NO_PARAMETER_WARNING = 'WARNING: found verify view without parameter'


def send_email(user, thread=True, expiry=None):
    send_inner(user, thread, expiry, 'MAIL')


def send_password(user, thread=True, expiry=None):
    send_inner(user, thread, expiry, 'PASSWORD')


def send_inner(user, thread, expiry, kind):
    try:
        user.save()

        token, expiry = default_token_generator.make_token(user, expiry, kind=kind)

        sender = _get_validated_field('EMAIL_FROM_ADDRESS')
        domain = _get_validated_field('EMAIL_PAGE_DOMAIN')
        subject = _get_validated_field(f'EMAIL_{kind}_SUBJECT')
        mail_plain = _get_validated_field(f'EMAIL_{kind}_PLAIN')
        mail_html = _get_validated_field(f'EMAIL_{kind}_HTML')

        args = (user, kind, token, expiry, sender, domain, subject, mail_plain, mail_html)
        if thread:
            t = Thread(target=send_email_thread, args=args)
            t.start()
        else:
            send_email_thread(*args)
    except AttributeError:
        raise InvalidUserModel('The user model you provided is invalid')


def send_email_thread(user, kind, token, expiry, sender, domain, subject, mail_plain, mail_html):
    domain += '/' if not domain.endswith('/') else ''

    def has_decorator(k):
        if callable(k):
            return k.__dict__.get(f'django_email_verification_{kind.lower()}_view_id', False)
        return False

    d = [v[0][0] for k, v in get_resolver(None).reverse_dict.items() if has_decorator(k)]
    w = [a[0] for a in d if a[1] == []]
    d = [a[0][:a[0].index('%')] for a in d if a[1] != []]

    if len(w) > 0:
        logger.warning(f'{DJANGO_EMAIL_VERIFICATION_NO_PARAMETER_WARNING}: {w}')

    if len(d) > 1:
        logger.error(f'{DJANGO_EMAIL_VERIFICATION_MORE_VIEWS_ERROR}: {d}')
        return

    context = {'token': token, 'expiry': expiry, 'user': user}

    if len(d) < 1:
        logger.info(DJANGO_EMAIL_VERIFICATION_NO_VIEWS_INFO)
    else:
        context['link'] = domain + d[0] + token

    subject = Template(subject).render(Context(context))

    text = render_to_string(mail_plain, context)

    html = render_to_string(mail_html, context)

    msg = EmailMultiAlternatives(subject, text, sender, [user.email])
    msg.attach_alternative(html, 'text/html')
    msg.send()


def _get_validated_field(field, default_type=None):
    if default_type is None:
        default_type = str
    try:
        d = getattr(settings, field)
        if d == "" or d is None or not isinstance(d, default_type):
            raise AttributeError
        return d
    except AttributeError:
        raise NotAllFieldCompiled(f"Field {field} missing or invalid")


def verify_password(token, password):
    valid, user = default_token_generator.check_token(token, kind='PASSWORD')
    if valid:
        callback = _get_validated_field('EMAIL_PASSWORD_CHANGED_CALLBACK', default_type=Callable)
        if hasattr(user, callback.__name__):
            getattr(user, callback.__name__)(password)
        else:
            callback(user, password)
        user.last_login = timezone.now()
        user.save()
        return valid, user
    return False, None


def verify_email(token):
    valid, user = default_token_generator.check_token(token, kind='MAIL')
    if valid:
        callback = _get_validated_field('EMAIL_VERIFIED_CALLBACK', default_type=Callable)
        if hasattr(user, callback.__name__):
            getattr(user, callback.__name__)()
        else:
            callback(user)
        user.last_login = timezone.now()
        user.save()
        return valid, user
    return False, None


@deprecation.deprecated(deprecated_in='0.3.0', details='use either verify_email() or verify_password()')
def verify_token(token):
    return verify_email(token)


def verify_email_view(func):
    func.django_email_verification_mail_view_id = True

    @functools.wraps(func)
    def verify_function_wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return verify_function_wrapper


def verify_password_view(func):
    func.django_email_verification_password_view_id = True

    @functools.wraps(func)
    def verify_function_wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return verify_function_wrapper


@deprecation.deprecated(deprecated_in='0.3.0', details='use either verify_email_view() or verify_password_view()')
def verify_view(func):
    func.django_email_verification_mail_view_id = True

    @functools.wraps(func)
    def verify_function_wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return verify_function_wrapper
