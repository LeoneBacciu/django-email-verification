import re
import time
from datetime import datetime

import pytest
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.http import int_to_base36, base36_to_int

from .. import send_email
from ..errors import NotAllFieldCompiled, InvalidUserModel


def get_mail_params(content):
    expiry = re.findall(r'\d{1,2}:\d{1,2}', content)[0]
    url = re.findall(r'(http|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?',
                     content)[0][-1]
    return url, expiry


@pytest.fixture
def test_user():
    user = get_user_model()(username='test_user', password='test_passwd', email='test@test.com')
    return user


@pytest.fixture
def wrong_token_template():
    match = render_to_string('confirm.html', {'success': False, 'user': None})
    return match


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

    assert email.subject == settings.EMAIL_MAIL_SUBJECT, "The subject changed"
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
    send_email(test_user, thread=False)
    email = mailoutbox[0]
    email_content = email.alternatives[0][0]
    url, _ = get_mail_params(email_content)
    response = client.get(url)
    match = render_to_string('confirm.html', {'success': True, 'user': test_user})
    assert response.content.decode() == match


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


def test_app_config():
    from .. import apps
    assert apps.DjangoEmailConfirmConfig.name == 'django_email_verification', "Wrong App name"
