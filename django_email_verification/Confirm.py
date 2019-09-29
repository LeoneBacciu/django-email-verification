from datetime import datetime as dt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from hashlib import sha224
from random import randint, shuffle
from smtplib import SMTP
from threading import Thread

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import get_resolver

from .errors import InvalidUserModel, EmailTemplateNotFound
from .errors import NotAllFieldCompiled


# Create your views here.
def verify(request, email_token):
    try:
        template = settings.EMAIL_PAGE_TEMPLATE
        return render(request, template, {'success': verifyToken(email_token)})
    except AttributeError:
        raise NotAllFieldCompiled('EMAIL_PAGE_TEMPLATE field not found')


def sendConfirm(user, **kwargs):
    from .models import User
    try:
        email = user.email
        user.is_active = False
        user.save()

        try:
            token = kwargs['token']
        except KeyError:
            alpha = [c for c in 'abcdefghijklmnopqrstuwxyz']
            shuffle(alpha)
            word = ''.join([a for a in alpha if randint(0, 1) == 1])
            token = str(sha224(bytes(email + str(dt.now()) + str(randint(1000, 9999)) + word, 'utf-8')).hexdigest())

        try:
            User.objects.get(user=user).delete()
        except User.DoesNotExist:
            pass

        user_email = User.objects.create(user=user, email_token=token)
        user_email.save()
        t = Thread(target=sendConfirm_thread, args=(email, token))
        t.start()
    except AttributeError:
        raise InvalidUserModel('The user model you provided is invalid')


def sendConfirm_thread(email, token):
    from .models import User
    try:
        sender = settings.EMAIL_SERVER
        domain = settings.EMAIL_PAGE_DOMAIN
        subject = settings.EMAIL_MAIL_SUBJECT
        address = settings.EMAIL_ADDRESS
        port = settings.EMAIL_PORT
        password = settings.EMAIL_PASSWORD
    except AttributeError:
        raise NotAllFieldCompiled('Compile all the fields in the settings')

    domain += '/' if not domain.endswith('/') else ''

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = email

    link = ''
    for k, v in get_resolver(None).reverse_dict.items():
        if k is verify and v[0][0][1][0]:
            addr = str(v[0][0][0])
            link = domain + addr[0: addr.index('%')] + token

    try:
        plain = settings.EMAIL_MAIL_PLAIN
        text = render_to_string(plain, {'link': link})
        part1 = MIMEText(text, 'plain')
        msg.attach(part1)
    except AttributeError:
        pass
    try:
        html = settings.EMAIL_MAIL_HTML
        html = render_to_string(html, {'link': link})
        part2 = MIMEText(html, 'html')
        msg.attach(part2)
    except AttributeError:
        pass

    if not msg.get_payload():
        User.objects.get(email_token=token).delete()
        raise EmailTemplateNotFound('No email template found')

    server = SMTP(sender, port)
    server.starttls()
    server.login(address, password)
    server.sendmail(sender, email, msg.as_string())
    server.quit()


def verifyToken(email_token):
    from .models import User
    try:
        user_email = User.objects.get(email_token=email_token)
        user = get_user_model().objects.get(email=user_email.user.email)
        user.is_active = True
        user.save()
        user_email.delete()
        return True
    except User.DoesNotExist:
        return False
