import logging
import re
import time
from datetime import datetime

import jwt
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import Client

from django_email_verification import send_password, send_email
from django_email_verification.confirm import DJANGO_EMAIL_VERIFICATION_MORE_VIEWS_ERROR, \
    DJANGO_EMAIL_VERIFICATION_NO_PARAMETER_WARNING, DJANGO_EMAIL_VERIFICATION_MALFORMED_URL, \
    DJANGO_EMAIL_VERIFICATION_NO_VIEWS_ERROR
from django_email_verification.errors import NotAllFieldCompiled, InvalidUserModel


class LogHandler(logging.StreamHandler):
    def __init__(self, levelname, match, callback):
        super().__init__()
        self.levelname = levelname
        self.match = match
        self.callback = callback
        self.warning_found = False
        self.error_found = False

    def emit(self, record):
        msg = self.format(record)
        if record.levelname == self.levelname and msg.startswith(self.match):
            self.callback()


def get_mail_params(content):
    expiry = re.findall(r'\d{1,2}:\d{1,2}', content)[0]
    url = re.findall(r'(http|https)://([\w_-]+(?:\.[\w_-]+)+)([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?',
                     content)
    url = url[0][-1] if len(url) > 0 else ''
    return url, expiry


def check_email_verification(test_user, mailoutbox, client):
    send_email(test_user, thread=False)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    time.sleep(1)
    url, _ = get_mail_params(email_content)
    response = client.get(url)
    match = render_to_string('confirm.html', {'success': True, 'user': test_user})
    assert response.content.decode() == match
    assert get_user_model().objects.get(email='test@test.com').is_active


def check_password_change(test_user, mailoutbox, client):
    send_password(test_user, thread=False)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    url, _ = get_mail_params(email_content)
    token = url.split('/')[-1]
    response = client.get(url)
    match = render_to_string('password_change.html', {'token': token})
    assert response.content.decode() == match

    new_password = 'new_password'
    response = client.post(url, {'password': new_password})
    match = render_to_string('confirm.html', {'success': True, 'user': test_user})
    assert response.content.decode() == match
    assert get_user_model().objects.get(email='test@test.com').check_password(new_password)


@pytest.fixture
def client():
    return Client(enforce_csrf_checks=True)


@pytest.fixture
def test_user():
    user = get_user_model()(username='test_user', password='test_passwd', email='test@test.com')
    return user


@pytest.fixture
def wrong_token_template():
    match = render_to_string('confirm.html', {'success': False, 'user': None})
    return match


@pytest.fixture
def wrong_password_token_template():
    match = render_to_string('password_changed.html', {'success': False, 'user': None})
    return match


@pytest.fixture
def test_user_with_class_method(settings):
    def verified_callback(self):
        self.is_active = True

    def password_changed(self, password):
        self.set_password(password)

    get_user_model().add_to_class('verified_callback', verified_callback)
    get_user_model().add_to_class('password_changed', password_changed)
    settings.EMAIL_VERIFIED_CALLBACK = get_user_model().verified_callback
    settings.EMAIL_PASSWORD_CHANGE_CALLBACK = get_user_model().password_changed
    user = get_user_model()(username='test_user_with_class_method', password='test_passwd', email='test@test.com')
    return user


@pytest.mark.django_db
def test_params_missing(test_user, settings, client):
    with pytest.raises(NotAllFieldCompiled):
        settings.EMAIL_FROM_ADDRESS = None
        send_email(test_user, thread=False)
    with pytest.raises(InvalidUserModel):
        send_email(None, thread=False)
    with pytest.raises(NotAllFieldCompiled):
        settings.EMAIL_MAIL_PAGE_TEMPLATE = None
        settings.EMAIL_PAGE_TEMPLATE = None
        client.get('/confirm/email/_')
    with pytest.raises(NotAllFieldCompiled):
        settings.EMAIL_MAIL_TOKEN_LIFE = None
        settings.EMAIL_TOKEN_LIFE = None
        send_email(test_user)
    with pytest.raises(NotAllFieldCompiled):
        settings.EMAIL_PASSWORD_PAGE_TEMPLATE = None
        client.get('/confirm/password/_')


@pytest.mark.django_db
def test_email_content(test_user, mailoutbox, settings):
    test_user.is_active = False
    send_email(test_user, thread=True)
    time.sleep(0.5)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    url, expiry = get_mail_params(email_content)

    assert email.subject == re.sub(r'({{.*}})', test_user.username, settings.EMAIL_MAIL_SUBJECT), "The subject changed"
    assert email.from_email == settings.EMAIL_FROM_ADDRESS, "The from_address changed"
    assert email.to == [test_user.email], "The to_address changed"
    assert len(expiry) > 0, f"No expiry time detected, {email_content}"
    assert len(url) > 0, "No link detected"


@pytest.mark.django_db
def test_email_custom_params(test_user, mailoutbox):
    s_expiry = datetime.now()
    test_user.is_active = False
    send_email(test_user, thread=False, expiry=s_expiry)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    _, expiry = get_mail_params(email_content)
    expiry = expiry.split(':')
    assert s_expiry.time().hour == int(expiry[0]) or s_expiry.time().hour - 12 == int(expiry[0])
    assert s_expiry.time().minute == int(expiry[1])


@pytest.mark.django_db
def test_email_extra_headers(test_user, settings, mailoutbox):
    settings.DEBUG = True
    s_expiry = datetime.now()
    test_user.is_active = False
    send_email(test_user, thread=False, expiry=s_expiry)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    link = email.extra_headers['LINK']
    token = email.extra_headers['TOKEN']
    assert link in email_content
    assert token in email_content


@pytest.mark.django_db
def test_email_correct(test_user, mailoutbox, client):
    test_user.is_active = False
    check_email_verification(test_user, mailoutbox, client)


@pytest.mark.django_db
def test_email_correct_user_model_method(test_user_with_class_method, mailoutbox, client):
    test_user_with_class_method.is_active = False
    assert hasattr(get_user_model(), settings.EMAIL_VERIFIED_CALLBACK.__name__)
    check_email_verification(test_user_with_class_method, mailoutbox, client)


@pytest.mark.django_db
def test_email_correct_multi_user(mailoutbox, settings, client):
    setattr(settings, 'EMAIL_MULTI_USER', True)
    test_user_1 = get_user_model().objects.create(username='test_user_1', password='test_passwd_1',
                                                  email='test@test.com')
    test_user_2 = get_user_model().objects.create(username='test_user_2', password='test_passwd_2',
                                                  email='test@test.com')
    test_user_1.is_active = False
    test_user_2.is_active = False
    test_user_1.save()
    test_user_2.save()
    send_email(test_user_1, thread=False)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    url, _ = get_mail_params(email_content)
    response = client.get(url)
    match = render_to_string('confirm.html', {'success': True, 'user': test_user_1})
    assert response.content.decode() == match
    assert list(get_user_model().objects.filter(email='test@test.com').values_list('is_active')) == [(True,), (False,)]


@pytest.mark.django_db
def test_email_wrong_link(client, wrong_token_template):
    url = '/confirm/email/dGVzdEB0ZXN0LmNvbE-agax3s-00348f02fabc98235547361a0fe69129b3b750f5'
    response = client.get(url)
    assert response.content.decode() == wrong_token_template, "Invalid token accepted"
    url = '/confirm/email/_'
    response = client.get(url)
    assert response.content.decode() == wrong_token_template, "Short token accepted"
    url = '/confirm/email/dGVzdEB0ZXN0LmNvbE++-agax3sert-00=00348f02fabc98235547361a0fe69129b3b750f5'
    response = client.get(url)
    assert response.content.decode() == wrong_token_template, "Long token accepted"


@pytest.mark.django_db
def test_email_wrong_different_timestamp(test_user, mailoutbox, client, wrong_token_template):
    test_user.is_active = False
    send_email(test_user, thread=False)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    url, _ = get_mail_params(email_content)

    token = url.split('/')
    token[-1] = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJleHAiOjE2NDc3MDgwODUuNzQ4NTM' \
                '5fQ.eubT3GdPIMKXefQeJ8ZWVTjnm5nzt2ehwh9nkdpoCes'
    url = '/'.join(token)

    response = client.get(url)
    assert response.content.decode() == wrong_token_template


@pytest.mark.django_db
def test_email_wrong_user(test_user, client, mailoutbox, wrong_token_template, settings):
    test_user.is_active = False
    send_email(test_user, thread=False)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    url, _ = get_mail_params(email_content)

    url = url.split('/')
    payload = jwt.decode(url[-1], settings.SECRET_KEY, algorithms=['HS256'])
    payload.update({'email': 'noemail@test.com'})
    url[-1] = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    url = '/'.join(url)

    response = client.get(url)
    assert response.content.decode() == wrong_token_template

    settings.EMAIL_MULTI_USER = True
    test_user.is_active = False
    send_email(test_user, thread=False)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    url, _ = get_mail_params(email_content)

    url = url.split('/')
    payload = jwt.decode(url[-1], settings.SECRET_KEY, algorithms=['HS256'])
    payload.update({'email': 'noemail@test.com'})
    url[-1] = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    url = '/'.join(url)

    response = client.get(url)
    assert response.content.decode() == wrong_token_template


@pytest.mark.django_db
def test_email_wrong_expired(test_user, mailoutbox, settings, client, wrong_token_template):
    settings.EMAIL_MAIL_TOKEN_LIFE = 1
    test_user.is_active = False
    send_email(test_user, thread=False)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    url, _ = get_mail_params(email_content)
    time.sleep(2)
    response = client.get(url)
    assert response.content.decode() == wrong_token_template


@pytest.mark.urls('django_email_verification.tests.urls_test_1')
@pytest.mark.django_db
def test_log_too_many_verify_view(test_user):
    error_raised = False

    def raise_error():
        nonlocal error_raised
        error_raised = True

    handler = LogHandler('ERROR', DJANGO_EMAIL_VERIFICATION_MORE_VIEWS_ERROR, raise_error)
    logger = logging.getLogger('django_email_verification')
    logger.addHandler(handler)
    test_user.is_active = False
    send_email(test_user, thread=False)
    assert error_raised, 'No error raised if multiple views are found'


@pytest.mark.urls('django_email_verification.tests.urls_test_2')
@pytest.mark.django_db
def test_log_no_verify_view(test_user):
    warning_raised = False

    def raise_warning():
        nonlocal warning_raised
        warning_raised = True

    handler = LogHandler('ERROR', DJANGO_EMAIL_VERIFICATION_NO_VIEWS_ERROR, raise_warning)
    logger = logging.getLogger('django_email_verification')
    logger.addHandler(handler)
    test_user.is_active = False
    send_email(test_user, thread=False)
    assert warning_raised, 'No warning raised if no view is found'


@pytest.mark.urls('django_email_verification.tests.urls_test_3')
@pytest.mark.django_db
def test_log_incomplete_verify_view(test_user):
    warning_raised = False

    def raise_warning():
        nonlocal warning_raised
        warning_raised = True

    handler = LogHandler('WARNING', DJANGO_EMAIL_VERIFICATION_NO_PARAMETER_WARNING, raise_warning)
    logger = logging.getLogger('django_email_verification')
    logger.addHandler(handler)
    test_user.is_active = False
    send_email(test_user, thread=False)
    assert warning_raised, 'No warning raised if incomplete urls are found'


@pytest.mark.django_db
def test_log_malformed_link(test_user, settings):
    setattr(settings, 'EMAIL_PAGE_DOMAIN', 'abcd')
    warning_raised = False

    def raise_warning():
        nonlocal warning_raised
        warning_raised = True

    handler = LogHandler('WARNING', DJANGO_EMAIL_VERIFICATION_MALFORMED_URL, raise_warning)
    logger = logging.getLogger('django_email_verification')
    logger.addHandler(handler)
    test_user.is_active = False
    send_email(test_user, thread=False)
    assert warning_raised, 'No warning raised if malformed url is not detected'


@pytest.mark.django_db
def test_password_content(test_user, mailoutbox, settings):
    send_password(test_user, thread=True)
    time.sleep(0.5)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    url, expiry = get_mail_params(email_content)

    assert email.subject == re.sub(r'({{.*}})', test_user.username,
                                   settings.EMAIL_PASSWORD_SUBJECT), "The subject changed"
    assert email.from_email == settings.EMAIL_FROM_ADDRESS, "The from_address changed"
    assert email.to == [test_user.email], "The to_address changed"
    assert len(expiry) > 0, f"No expiry time detected, {email_content}"
    assert len(url) > 0, "No link detected"


@pytest.mark.django_db
def test_password_correct(test_user, mailoutbox, client):
    check_password_change(test_user, mailoutbox, client)


@pytest.mark.django_db
def test_password_correct_user_model_method(test_user_with_class_method, mailoutbox, client):
    test_user_with_class_method.is_active = False
    assert hasattr(get_user_model(), settings.EMAIL_PASSWORD_CHANGE_CALLBACK.__name__)
    check_password_change(test_user_with_class_method, mailoutbox, client)


@pytest.mark.django_db
def test_password_wrong_link(client, wrong_password_token_template):
    url = '/confirm/password/dGVzdEB0ZXN0LmNvbE-agax3s-00348f02fabc98235547361a0fe69129b3b750f5'
    response = client.post(url, {'password': 'test'})
    assert response.content.decode() == wrong_password_token_template, "Invalid token accepted"


@pytest.mark.django_db
def test_password_wrong_email_link_used(test_user, mailoutbox, client):
    send_email(test_user, thread=False)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    url, _ = get_mail_params(email_content)
    url = url.replace('email', 'password')
    new_password = 'new_password'
    response = client.post(url, {'password': new_password})
    match = render_to_string('confirm.html', {'success': False, 'user': None})
    assert response.content.decode() == match
    assert not get_user_model().objects.get(email='test@test.com').check_password(new_password)


def test_app_config():
    from .. import apps
    assert apps.DjangoEmailConfirmConfig.name == 'django_email_verification', "Wrong App name"
