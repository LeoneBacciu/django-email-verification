import logging
import re
import time
from datetime import datetime
from django.conf import settings

import pytest
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.http import int_to_base36, base36_to_int

from django_email_verification import send_email
from django_email_verification.errors import NotAllFieldCompiled, InvalidUserModel
from django_email_verification.confirm import DJANGO_EMAIL_VERIFICATION_MORE_VIEWS_ERROR, \
    DJANGO_EMAIL_VERIFICATION_NO_VIEWS_ERROR, DJANGO_EMAIL_VERIFICATION_NO_PARAMETER_WARNING


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
    url = re.findall(r'(http|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?',
                     content)[0][-1]
    return url, expiry

def check_verification(test_user, mailoutbox, client):
    send_email(test_user, thread=False)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    url, _ = get_mail_params(email_content)
    response = client.get(url)
    match = render_to_string('confirm.html', {'success': True, 'user': test_user})
    assert response.content.decode() == match
    assert get_user_model().objects.get(email='test@test.com').is_active

    
@pytest.fixture
def test_user():
    user = get_user_model()(username='test_user', password='test_passwd', email='test@test.com')
    return user


@pytest.fixture
def wrong_token_template():
    match = render_to_string('confirm.html', {'success': False, 'user': None})
    return match

@pytest.fixture
def test_user_with_class_method(settings):
    def verified_callback(self):
        self.is_active=True
    get_user_model().add_to_class('verified_callback', verified_callback)
    settings.EMAIL_VERIFIED_CALLBACK = get_user_model().verified_callback
    user = get_user_model()(username='test_user_with_class_method', password='test_passwd', email='test@test.com')
    return user



@pytest.mark.django_db
def test_missing_params(test_user, settings, client):
    with pytest.raises(NotAllFieldCompiled):
        settings.EMAIL_FROM_ADDRESS = None
        send_email(test_user, thread=False)
    with pytest.raises(InvalidUserModel):
        send_email(None, thread=False)
    with pytest.raises(NotAllFieldCompiled):
        settings.EMAIL_PAGE_TEMPLATE = None
        url = '/email/_'
        client.get(url)


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
    send_email(test_user, thread=False, custom_salt='test_salt', expiry=s_expiry)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    _, expiry = get_mail_params(email_content)
    expiry = expiry.split(':')
    assert s_expiry.time().hour == int(expiry[0]) or s_expiry.time().hour - 12 == int(expiry[0])
    assert s_expiry.time().minute == int(expiry[1])


@pytest.mark.django_db
def test_email_link_correct(test_user, mailoutbox, client):
    test_user.is_active = False
    check_verification(test_user, mailoutbox, client)

@pytest.mark.django_db
def test_email_link_correct_user_model_method(test_user_with_class_method, mailoutbox, client):
    test_user_with_class_method.is_active = False
    assert hasattr(get_user_model(), settings.EMAIL_VERIFIED_CALLBACK.__name__)
    check_verification(test_user_with_class_method, mailoutbox, client)


@pytest.mark.django_db
def test_email_link_wrong(client, wrong_token_template):
    url = '/email/dGVzdEB0ZXN0LmNvbE-agax3s-00348f02fabc98235547361a0fe69129b3b750f5'
    response = client.get(url)
    assert response.content.decode() == wrong_token_template, "Invalid token accepted"
    url = '/email/_'
    response = client.get(url)
    assert response.content.decode() == wrong_token_template, "Short token accepted"
    url = '/email/dGVzdEB0ZXN0LmNvbE++-agax3sert-00=00348f02fabc98235547361a0fe69129b3b750f5'
    response = client.get(url)
    assert response.content.decode() == wrong_token_template, "Long token accepted"


@pytest.mark.django_db
def test_token_different_timestamp(test_user, mailoutbox, client, wrong_token_template):
    test_user.is_active = False
    send_email(test_user, thread=False)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    url, _ = get_mail_params(email_content)

    # Increment timestamp
    token = url.split('-')
    token[1] = int_to_base36(base36_to_int(token[1]) + 1)
    url = '-'.join(token)

    response = client.get(url)
    assert response.content.decode() == wrong_token_template


@pytest.mark.django_db
def test_token_expired(test_user, mailoutbox, settings, client, wrong_token_template):
    settings.EMAIL_TOKEN_LIFE = 1
    test_user.is_active = False
    send_email(test_user, thread=False)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    url, _ = get_mail_params(email_content)
    time.sleep(2)
    response = client.get(url)
    assert response.content.decode() == wrong_token_template


@pytest.mark.django_db
def test_multi_user(mailoutbox, settings, client):
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


@pytest.mark.urls('django_email_verification.tests.urls_test_1')
@pytest.mark.django_db
def test_too_many_verify_view(test_user):
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
def test_no_verify_view(test_user):
    error_raised = False

    def raise_error():
        nonlocal error_raised
        error_raised = True

    handler = LogHandler('ERROR', DJANGO_EMAIL_VERIFICATION_NO_VIEWS_ERROR, raise_error)
    logger = logging.getLogger('django_email_verification')
    logger.addHandler(handler)
    test_user.is_active = False
    send_email(test_user, thread=False)
    assert error_raised, 'No error raised if no views are found'


@pytest.mark.django_db
def test_incomplete_verify_view(test_user):
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


def test_app_config():
    from .. import apps
    assert apps.DjangoEmailConfirmConfig.name == 'django_email_verification', "Wrong App name"
