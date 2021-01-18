from base64 import urlsafe_b64decode, urlsafe_b64encode
from binascii import Error as b64Error
from threading import Thread
from typing import Callable

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import get_resolver
from django.utils import timezone

from .errors import InvalidUserModel, NotAllFieldCompiled
from .token import default_token_generator


def send_email(user, **kwargs):
    try:
        user.save()

        if kwargs.get('custom_salt'):
            default_token_generator.key_salt = kwargs['custom_salt']

        try:
            token = kwargs['token']
            expiry = kwargs['expiry']
        except KeyError:
            token, expiry = default_token_generator.make_token(user)

        t = Thread(target=send_email_thread, args=(user, token, expiry))
        t.start()
    except AttributeError:
        raise InvalidUserModel('The user model you provided is invalid')


def send_email_thread(user, token, expiry):
    sender = _get_validated_field('EMAIL_FROM_ADDRESS')
    domain = _get_validated_field('EMAIL_PAGE_DOMAIN')
    subject = _get_validated_field('EMAIL_MAIL_SUBJECT')
    mail_plain = _get_validated_field('EMAIL_MAIL_PLAIN')
    mail_html = _get_validated_field('EMAIL_MAIL_HTML')
    path = f'{urlsafe_b64encode(str(user.email).encode()).decode()}/{token}'

    domain += '/' if not domain.endswith('/') else ''

    from .views import verify
    link = ''
    for k, v in get_resolver(None).reverse_dict.items():
        if k is verify and v[0][0][1][0]:
            addr = str(v[0][0][0])
            link = domain + addr[0: addr.index('%')] + path

    context = {'link': link, 'expiry': expiry, 'user': user}

    text = render_to_string(mail_plain, context)

    html = render_to_string(mail_html, context)

    msg = EmailMultiAlternatives(subject, text, sender, [user.email])
    msg.attach_alternative(html, 'text/html')
    msg.send()


def _get_validated_field(field, raise_error=True, default_type=None):
    if default_type is None:
        default_type = str
    try:
        d = getattr(settings, field)
        if d == "" or d is None or not isinstance(d, default_type):
            raise AttributeError
        return d
    except AttributeError:
        if raise_error:
            raise NotAllFieldCompiled(f"Field {field} missing or invalid")
        return None


def verify_token(email, email_token):
    try:
        users = get_user_model().objects.filter(email=urlsafe_b64decode(email).decode("utf-8"))
        for user in users:
            valid = default_token_generator.check_token(user, email_token)
            if valid:
                callback = _get_validated_field('EMAIL_VERIFIED_CALLBACK', default_type=Callable)
                callback(user)
                user.last_login = timezone.now()
                user.save()
                return valid
    except b64Error:
        pass
    return False
