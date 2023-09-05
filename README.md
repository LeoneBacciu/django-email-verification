# Django Email Verification

[![PyPI](https://img.shields.io/pypi/v/django-email-verification?style=flat-square&logo=pypi&color=yellow)](https://pypi.org/project/django-email-verification/)
[![PyPI - License](https://img.shields.io/pypi/l/django-email-verification?style=flat-square&logo=open-source-initiative)](https://github.com/LeoneBacciu/django-email-verification/blob/version-0.1.0/LICENSE)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/LeoneBacciu/django-email-verification/test.yaml?style=flat-square&logo=github-actions)](https://github.com/LeoneBacciu/django-email-verification/actions)
[![codecov](https://img.shields.io/codecov/c/github/LeoneBacciu/django-email-verification?token=97DDVD3MGW&style=flat-square&logo=codecov)](https://codecov.io/gh/LeoneBacciu/django-email-verification)

<p align="center">
  <img src="https://github.com/LeoneBacciu/django-email-verification/blob/master/icon.png?raw=True" width="300px" alt="icon">
</p>

<p align="center">
Do you like my work and want to support me?<br/><br/>
<a href="https://www.buymeacoffee.com/LeoneBacciu" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>
</p>

> ## 🚧 Work in progress 🚧
> The package now also provides all the feature needed for **password recovery**, but the documentation is not ready
> yet. \
> Thanks for your patience!

## Requirements

+ Python >= 3.8
+ Django >= 4.2

## General concept


Here is a simple Sequence Diagram of the email verification process:

```mermaid
sequenceDiagram
    actor U as User
    participant D as django-email-verification
    participant C as Your Code
    
    U -->> C: Creates an Account
    note over C: Set User as inactive
    C ->> D: Call send_email
    D -)+ U: Email with Activation Link
    U -)- C: Link clicked
    C ->> D: Request forwarded
    critical Token Validation
       option Valid 
           D ->> C: Run Callback
           D ->> U: Render Success Page
       option Invalid
           D ->> U: Render Error Page
    end
```

And here is a simple Sequence Diagram of the password recovery process:

```mermaid
sequenceDiagram
    actor U as User
    participant D as django-email-verification
    participant C as Your Code
    
    U -->> C: Click on Recover Password
    C ->> D: Call send_password
    D -)+ U: Email with Password Change Link
    U -)- C: Link clicked
    C ->> D: Request forwarded
    critical Token Validation
       option Valid 
           D ->> U: Render Password Change View
           U ->> D: Submit new Password
           D ->> C: Run Callback
           D ->> U: Render Success Page
       option Invalid
           D ->> U: Render Error Page
    end
```

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
def email_verified_callback(user):
    user.is_active = True
    
def password_change_callback(user, password):
  user.set_password(password)


EMAIL_FROM_ADDRESS = 'noreply@aliasaddress.com'
EMAIL_PAGE_DOMAIN = 'https://mydomain.com/'
EMAIL_MULTI_USER = False  # optional (defaults to False)

EMAIL_MAIL_SUBJECT = 'Confirm your email {{ user.username }}'
EMAIL_MAIL_HTML = 'mail_body.html'
EMAIL_MAIL_PLAIN = 'mail_body.txt'
EMAIL_MAIL_PAGE_TEMPLATE = 'email_success_template.html'
EMAIL_MAIL_TOKEN_LIFE = 60 * 60 # one hour
EMAIL_MAIL_CALLBACK = email_verified_callback

EMAIL_PASSWORD_SUBJECT = 'Change your password {{ user.username }}'
EMAIL_PASSWORD_HTML = 'password_body.html'
EMAIL_PASSWORD_PLAIN = 'password_body.txt'
EMAIL_PASSWORD_PAGE_TEMPLATE = 'password_change_template.html'
EMAIL_PASSWORD_CHANGED_PAGE_TEMPLATE = 'password_changed_template.html'
EMAIL_PASSWORD_TOKEN_LIFE = 60 * 10 # 10 minutes
EMAIL_PASSWORD_CALLBACK = password_change_callback


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
+ `EMAIL_MAIL_TOKEN_LIFE`: the lifespan of the email link (in seconds).
+ `EMAIL_MAIL_PAGE_TEMPLATE`: the template of the success/error view.
+ `EMAIL_PAGE_DOMAIN`: the domain of the confirmation link (usually your site's domain).
+ `EMAIL_MULTI_USER`: (optional) if `True` an error won't be thrown if multiple users with the same email are present (
  just one will be activated)

For the Django Email Backend fields look at the
official [documentation](https://docs.djangoproject.com/en/3.1/topics/email/).

The `EMAIL_VERIFIED_CALLBACK` can be a function on the `AUTH_USER_MODEL`, for example:
```python
EMAIL_VERIFIED_CALLBACK = get_user_model().verified_callback
```
The function will receive no arguments.

## Templates examples

The `EMAIL_MAIL_SUBJECT` should look like this; (`{{ link }}`(`str`), `{{ expiry }}`(`datetime`) and `user`(`Model`) are
passed during the rendering).

```python
EMAIL_MAIL_SUBJECT = 'Confirm your email {{ user.username }}'
```

The `EMAIL_MAIL_HTML` should look like this; (`{{ link }}`(`str`), `{{ expiry }}`(`datetime`) and `user`(`Model`) are
passed during the rendering).

```html
<h1>You are almost there, {{ user.username }}!</h1><br>
<h2>Please click <a href="{{ link }}">here</a> to confirm your account</h2>
<h2>The token expires on {{ expiry|time:"TIME_FORMAT" }}</h2>
```

The `EMAIL_MAIL_PLAIN` should look like this; (`{{ link }}`(`str`), `{{ expiry }}`(`datetime`) and `user`(`Model`) are
passed during the rendering).

```text
You are almost there, {{ user.username }}!
Please click the following link to confirm your account: {{ link }}
The token expires on {{ expiry|time:"TIME_FORMAT" }}
```

The `EMAIL_MAIL_PAGE_TEMPLATE` should look like this; (`{{ success }}`(`bool`), `{{ user }}`(`Model`)
and `{{ request }}`(`WSGIRequest`) are passed during the rendering).

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

> **NOTE**: By default the email is sent asynchronously, which is the suggested behaviour, if this is a problem (for example if you are running synchronous tests), you can pass the parameter `thread`: 
>
>     send_email(user, thread=False) # When this function returns, the email has been sent

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

  + if it corresponds to a pending token it renders the `EMAIL_MAIL_PAGE_TEMPLATE` passing `success=True` and deletes the token
  + if it doesn't correspond it renders the `EMAIL_MAIL_PAGE_TEMPLATE` passing `success=False`


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
  ```

  ```python
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


## Testing

If you are using django-email-verification and you want to test the email, if settings.DEBUG == True, then two items
will be added to the email headers.
You can obtain these by checking the django.core.mail outbox, which will have a non-zero length if an email has been
sent. Retrieve the email and obtain the link (includes token) or the token to use in your code.

```python
from django.core import mail

...
test
body
...

try:
  email = mail.outbox[0]
  link = mail.extra_headers['LINK']
  token = mail.extra_headers['TOKEN']
  browser.visit(link)  # verifies token...
except AttributeError:
  logger.warn("no email")
```

For the email to be in the inbox, you will need to use the correct email backend. Use either:
```python
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
```
or:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

You can use any Django email backend and also your custom one.

If you want to run the builtin tests, clone the project and execute:
```commandline
coverage run --source=django_email_verification -m pytest && coverage report -m
```
(You will need [coverage](https://pypi.org/project/coverage/), [pytest](https://pypi.org/project/pytest/) and [pytest-django](https://pypi.org/project/pytest-django/))

### Logo copyright:

Logo by <a href="https://github.com/filippoveggo" title="Flippo Veggo">Filippo Veggo</a>
<div>"Django and the Django logo are registered trademarks of Django Software Foundation.<br/>Usage of the Django trademarks are subject to the Django Trademark licensing Agreement."</div>
<div>Icons made by <a href="https://www.flaticon.com/authors/kiranshastry" title="Kiranshastry">Kiranshastry</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a></div>
<div>Icons made by <a href="https://www.flaticon.com/authors/pixel-perfect" title="Pixel perfect">Pixel perfect</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a></div>
