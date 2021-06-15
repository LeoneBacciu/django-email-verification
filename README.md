# Django Email Verification

[![PyPI](https://img.shields.io/pypi/v/django-email-verification?color=yellowgreen&logo=pypi)](https://pypi.org/project/django-email-verification/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-email-verification?logo=python)](https://www.python.org/downloads/release/python-380/)
[![PyPI - Django Version](https://img.shields.io/pypi/djversions/django-email-verification?logo=django)](https://docs.djangoproject.com/en/3.1/releases/3.1/)
[![PyPI - License](https://img.shields.io/pypi/l/django-email-verification?logo=open-source-initiative)](https://github.com/LeoneBacciu/django-email-verification/blob/version-0.1.0/LICENSE)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/LeoneBacciu/django-email-verification/Upload%20Python%20Package?logo=github-actions)](https://github.com/LeoneBacciu/django-email-verification/actions)
[![codecov](https://codecov.io/gh/LeoneBacciu/django-email-verification/branch/master/graph/badge.svg?token=97DDVD3MGW)](https://codecov.io/gh/LeoneBacciu/django-email-verification)

<p align="center">
  <img src="https://github.com/LeoneBacciu/django-email-verification/blob/master/icon.png?raw=True" width="300px" alt="icon">
</p>

## Requirements

+ Python >= 3.8
+ Django >= 3.1

## General concept

![Schema](https://github.com/LeoneBacciu/django-email-verification/blob/master/email_flow.png?raw=True "Flow")

## Installation

You can install by:

```commandline
pip3 install django-email-verification
```

and import by:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    ...
    'django_email_verification',  # you have to add this
]
```

## Settings parameters

You have to add these parameters to the settings, you have to include all of them except the last one:

```python
def verified_callback(user):
    user.is_active = True


EMAIL_VERIFIED_CALLBACK = verified_callback
EMAIL_FROM_ADDRESS = 'noreply@aliasaddress.com'
EMAIL_MAIL_SUBJECT = 'Confirm your email'
EMAIL_MAIL_HTML = 'mail_body.html'
EMAIL_MAIL_PLAIN = 'mail_body.txt'
EMAIL_TOKEN_LIFE = 60 * 60
EMAIL_PAGE_TEMPLATE = 'confirm_template.html'
EMAIL_PAGE_DOMAIN = 'http://mydomain.com/'
EMAIL_MULTI_USER = True  # optional (defaults to False)

# For Django Email Backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'mymail@gmail.com'
EMAIL_HOST_PASSWORD = 'mYC00lP4ssw0rd'  # os.environ['password_key'] suggested
EMAIL_USE_TLS = True


```

In detail:

+ `EMAIL_VERIFIED_CALLBACK`: the function that will be called when the user successfully verifies the email. Takes the
  user object as argument.
+ `EMAIL_FROM_ADDRESS`: this can be the same as `EMAIL_HOST_USER` or an alias address if required.
+ `EMAIL_MAIL_`:
    * `SUBJECT`: the mail default subject.
    * `HTML`: the mail body template in form of html.
    * `PLAIN`: the mail body template in form of .txt file.
+ `EMAIL_TOKEN_LIFE`: the lifespan of the email link (in seconds).
+ `EMAIL_PAGE_TEMPLATE`: the template of the success/error view.
+ `EMAIL_PAGE_DOMAIN`: the domain of the confirmation link (usually your site's domain).
+ `EMAIL_MULTI_USER`: (optional) if `True` an error won't be thrown if multiple users with the same email are present (
  just one will be activated)

For the Django Email Backend fields look at the
official [documentation](https://docs.djangoproject.com/en/3.1/topics/email/).

## Templates examples

The `EMAIL_MAIL_SUBJECT` should look like this (`{{ link }}`(`str`), `{{ expiry }}`(`datetime`) and `user`(`Model`) are
passed during the rendering):

```python
EMAIL_MAIL_SUBJECT = 'Confirm your email {{ user.username }}'
```

The `EMAIL_MAIL_HTML` should look like this (`{{ link }}`(`str`), `{{ expiry }}`(`datetime`) and `user`(`Model`) are
passed during the rendering):

```html
<h1>You are almost there, {{ user.username }}!</h1><br>
<h2>Please click <a href="{{ link }}">here</a> to confirm your account</h2>
<h2>The token expires on {{ expiry|time:"TIME_FORMAT" }}</h2>
```

The `EMAIL_MAIL_PLAIN` should look like this (`{{ link }}`(`str`), `{{ expiry }}`(`datetime`) and `user`(`Model`) are
passed during the rendering):

```text
You are almost there, {{ user.username }}!
Please click the following link to confirm your account: {{ link }}
The token expires on {{ expiry|time:"TIME_FORMAT" }}
```

The `EMAIL_PAGE_TEMPLATE` should look like this (`{{ success }}`(`bool`), `{{ user }}`(`Model`)
and `{{ request }}`(`WSGIRequest`) are passed during the rendering):

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Confirmation</title>
</head>
<body>
{% if success %}
{{ user.username }}, your account is confirmed!
{% else %}
Error, invalid token!
{% endif %}
</body>
</html>
```

## Email sending

After you have created the user you can send the confirm email

```python
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django_email_verification import send_email


def my_functional_view(request):
    ...
    user = get_user_model().objects.create(username=username, password=password, email=email)
    user.is_active = False  # Example
    send_email(user)
    return render(...)
```

`send_email(user)` sends an email with the defined template (and the pseudo-random generated token) to the user.

> **_IMPORTANT:_** You have to manually set the user to inactive before sending the email.

If you are using class based views, then it is necessary to call the superclass before calling the `send_confirm`
method.

```python
from django.views.generic.edit import FormView
from django_email_verification import send_email


class MyClassView(FormView):

    def form_valid(self, form):
        user = form.save()
        returnVal = super(MyClassView, self).form_valid(form)
        send_email(user)
        return returnVal
```

## Token verification

There are two ways to get the token verified:

+ The first one is the simplest: you just have to include the app urls in `urls.py`

    ```python
    from django.contrib import admin
    from django.urls import path, include
    from django_email_verification import urls as email_urls  # include the urls

    urlpatterns = [
      path('admin/', admin.site.urls),
      ...
      path('email/', include(email_urls)),  # connect them to an arbitrary path
    ]
  ```
  When a request arrives to `https.//mydomain.com/email/<token>` the package verifies the token and:

  + if it corresponds to a pending token it renders the `EMAIL_PAGE_TEMPLATE` passing `success=True` and deletes the token
  + if it doesn't correspond it renders the `EMAIL_PAGE_TEMPLATE` passing `success=False`


+ The second one is more customizable: you can build your own view for verification, mark it as `@verify_view`, verify the token manually with the function `verify_token(token)` and execute your custom logic,
  here's how:

  ```python
  ### For the view

  from django.http import HttpResponse
  from django_email_verification import verify_view, verify_token


  @verify_view
  def confirm(request, token):
      success, user = verify_token(token)
      return HttpResponse(f'Account verified, {user.username}' if success else 'Invalid token')


  ### For the urls
  from django.urls import path

  urlpatterns = [
      ...
      path('email/<str:token>/', confirm), # remember to set the "token" parameter in the url!
      ...
  ]
  ```
  > **_IMPORTANT:_** the path must **NOT** have the `name` attribute set

  The library makes sure one and only one `@verify_view` is present and throws an error if this condition is not met.



## Console backend for development

If you want to use the console email backend provided by django, then define:

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

You can use all the django email backends and also your custom one.

## Custom salt for token generation

You can define a custom salt to be used in token generation in your settings file. Simply define:

```python
CUSTOM_SALT = 'xxxxxxxxxxxxxxxxxxxxxxx'
```

in your settings.py.

### Logo copyright:

Logo by by <a href="https://github.com/filippoveggo" title="Flippo Veggo">Filippo Veggo</a>
<div>"Django and the Django logo are registered trademarks of Django Software Foundation.<br/>Usage of the Django trademarks are subject to the Django Trademark licensing Agreement."</div>
<div>Icons made by <a href="https://www.flaticon.com/authors/kiranshastry" title="Kiranshastry">Kiranshastry</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a></div>
<div>Icons made by <a href="https://www.flaticon.com/authors/pixel-perfect" title="Pixel perfect">Pixel perfect</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a></div>
