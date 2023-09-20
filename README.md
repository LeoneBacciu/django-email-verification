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

The app is build to be as little opinionated as possible, every action it can perform can be replaced by custom code,
and everything else will continue working just the same.\
For both Email Verification and Password Recovery, the features can be divided into:

1. [Email Sending](#email-sending)
2. [Verification / Recovery View](#verification--recovery-view)

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
# settings.py

def email_verified_callback(user):
    user.is_active = True


def password_change_callback(user, password):
    user.set_password(password)


# Global Package Settings
EMAIL_FROM_ADDRESS = 'noreply@aliasaddress.com'  # mandatory
EMAIL_PAGE_DOMAIN = 'https://mydomain.com/'  # mandatory (unless you use a custom link)
EMAIL_MULTI_USER = False  # optional (defaults to False)

# Email Verification Settings (mandatory for email sending)
EMAIL_MAIL_SUBJECT = 'Confirm your email {{ user.username }}'
EMAIL_MAIL_HTML = 'mail_body.html'
EMAIL_MAIL_PLAIN = 'mail_body.txt'
EMAIL_MAIL_TOKEN_LIFE = 60 * 60  # one hour

# Email Verification Settings (mandatory for builtin view)
EMAIL_MAIL_PAGE_TEMPLATE = 'email_success_template.html'
EMAIL_MAIL_CALLBACK = email_verified_callback

# Password Recovery Settings (mandatory for email sending)
EMAIL_PASSWORD_SUBJECT = 'Change your password {{ user.username }}'
EMAIL_PASSWORD_HTML = 'password_body.html'
EMAIL_PASSWORD_PLAIN = 'password_body.txt'
EMAIL_PASSWORD_TOKEN_LIFE = 60 * 10  # 10 minutes

# Password Recovery Settings (mandatory for builtin view)
EMAIL_PASSWORD_PAGE_TEMPLATE = 'password_changed_template.html'
EMAIL_PASSWORD_CHANGE_PAGE_TEMPLATE = 'password_change_template.html'
EMAIL_PASSWORD_CALLBACK = password_change_callback

# For Django Email Backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'mymail@gmail.com'
EMAIL_HOST_PASSWORD = 'mYC00lP4ssw0rd'  # os.environ['password_key'] suggested
EMAIL_USE_TLS = True
```

For simplicity, I will refer to both `XX_MAIL_XX` and `XX_PASSWORD_XX` by writing `XX_{MAIL|PASSWORD}_XX`.

In detail:

+ `EMAIL_FROM_ADDRESS`: this can be the same as `EMAIL_HOST_USER` or an alias address if required.
+ `EMAIL_PAGE_DOMAIN`: the domain of the confirmation link (usually your site's domain).
+ `EMAIL_MULTI_USER`: (optional) if `True` an error won't be thrown if multiple users with the same email are present (
  just one will be activated)
+ `EMAIL_MAIL_CALLBACK`: will be called when the user successfully verifies the email. Can be a function (taking the
  user object as a parameter) or a method on the user object (no arguments) [^1].
+ `EMAIL_PASSWORD_CALLBACK`: will be called when the user successfully submits a new password. Can be a function (taking the
  user object and the new password as parameters) or a method on the user object (taking the new password as a parameter)[^1].
+ `EMAIL_{MAIL|PASSWORD}_`: are all django templates:
    * `SUBJECT`: the mail default subject.
    * `HTML`: the mail body template in form of html.
    * `PLAIN`: the mail body template in form of .txt file.
+ `EMAIL_{MAIL|PASSWORD}_TOKEN_LIFE`: the lifespan of the email link (in seconds).
+ `EMAIL_{MAIL|PASSWORD}_PAGE_TEMPLATE`: the template of the success/error view. Takes `{success: bool, user: Model, request: WSGIRequest}` as parameters.
+ `EMAIL_PASSWORD_CHANGE_TEMPLATE`: the template for the page with the form to submit a new password. Must send a POST request to the same address, with the field `password` in the payload.

For the Django Email Backend fields look at the
official [documentation](https://docs.djangoproject.com/en/4.2/topics/email/).


## Email Sending

The functions in charge of sending the emails are the following:

```python
send_email(user, thread=True, expiry=None, context=None)
send_password(user, thread=True, expiry=None, context=None)
```

The fields are:
 - `user` (`Model`): the user you want to send the email to
 - `thread` (`bool`): whether to send the email asynchronously or not
 - `expiry` (`datetime`): custom token expiry date (different from `datetime.now() + EMAIL_{MAIL|PASSWORD}_TOKEN_LIFE`)
 - `context` (`dict`): additional context for the email template

> **NOTE**: By default the email is sent asynchronously, which is the suggested behaviour, if this is a problem (for
> example if you are running synchronous tests), you can pass the parameter `thread=False`.

```python
# views.py

from django.shortcuts import render
from django.contrib.auth import get_user_model
from django_email_verification import send_email


def create_account_functional_view(request):
    ...
    user = get_user_model().objects.create(username=username, password=password, email=email)
    user.is_active = False  # Example
    send_email(user)
    return render(...)


def recover_password_functional_view(request):
    ...
    send_password(user)
    return render(...)
```

`send_email(user)` and `send_password(user)` send an email with the defined template (and the pseudo-random generated token) to the user.

> **_IMPORTANT:_** For email verification, you have to manually set the user to inactive before sending the email.

If you are using class based views, then it is necessary to call the superclass before calling the `send_email`
method.

```python
# views.py

from django.views.generic.edit import FormView
from django_email_verification import send_email


class CreateAccountClassView(FormView):

    def form_valid(self, form):
        user = form.save()
        return_val = super(CreateAccountClassView, self).form_valid(form)
        send_email(user)
        return return_val
```


### Templates examples

The `EMAIL_{MAIL|PASSWORD}_SUBJECT` is a template that receives `{{ token }}`(`str`), `{{ link }}`(`str`), `{{ expiry }}`(`datetime`) and `user`(`Model`) (plus your custom context) as arguments,
it might look something like this:

```python
EMAIL_MAIL_SUBJECT = 'Confirm your email {{ user.username }}'
EMAIL_PASSWORD_SUBJECT = 'Change password request for {{ user.username }}'
```

The `EMAIL_{MAIL|PASSWORD}_HTML` is a template that receives `{{ token }}`(`str`), `{{ link }}`(`str`), `{{ expiry }}`(`datetime`) and `user`(`Model`) (plus your custom contex) as arguments,
it might look something like this:

```html
<h1>You are almost there, {{ user.username }}!</h1><br>
<h2>Please click <a href="{{ link }}">here</a> to confirm your account</h2>
<h2>The token expires on {{ expiry|time:"TIME_FORMAT" }}</h2>
```

The `EMAIL_{MAIL|PASSWORD}_PLAIN` is a template that receives `{{ token }}`(`str`), `{{ link }}`(`str`), `{{ expiry }}`(`datetime`) and `user`(`Model`) (plus your custom contex) as arguments,
it might look something like this:

```text
You are almost there, {{ user.username }}!
Please click the following link to confirm your account: {{ link }}
The token expires on {{ expiry|time:"TIME_FORMAT" }}
```

## Verification / Recovery View

### Builtin Method

The easiest way to recieve the token is to use the builtin views.
To do so you just need to include the application's urls and define the necessary Django templates.

```python
# urls.py

from django.contrib import admin
from django.urls import path, include
from django_email_verification import urls as email_urls  # include the urls

urlpatterns = [
  ...
  path('email/', include(email_urls)),  # connect them to an arbitrary path
  ...
]
```
When a request arrives to `https.//mydomain.com/email/email/<token>` the package verifies the token and:
 + if it corresponds to a pending token it renders the `EMAIL_MAIL_PAGE_TEMPLATE` passing `success=True`
 + if it doesn't correspond it renders the `EMAIL_MAIL_PAGE_TEMPLATE` passing `success=False`

If the token is correct, `EMAIL_MAIL_CALLBACK` is called before the page is returned.

The `EMAIL_MAIL_PAGE_TEMPLATE` is a template that receives `{{ success }}`(`bool`), `{{ user }}`(`Model`) and `{{ request }}`(`WSGIRequest`) as arguments,
it might look something like this:

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

When a request arrives to `https.//mydomain.com/email/password/<token>` the package renders `EMAIL_PASSWORD_CHANGE_TEMPLATE`.
This view should present a form that submits a POST request to the same url, passing a `password` field in the body.

The `EMAIL_PASSWORD_CHANGE_TEMPLATE` is a template that receives `{{ user }}`(`Model`) and `{{ request }}`(`WSGIRequest`) as arguments,
it might look something like this:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Password Change</title>
</head>
<body>
{{ user.username }}, set your new password:
<form method="post">
  <label for="password">New Password:</label>
  <input type="password" id="password" name="password">
  <input type="submit" value="Submit">
</form>
</body>
</html>
```

Once the POST request it's submitted, the server verifies the token and:
+ if it corresponds to a pending token it renders the `EMAIL_PASSWORD_TEMPLATE`
+ if it doesn't correspond it renders the `EMAIL_PASSWORD_TEMPLATE` passing `success=False`

If the token is correct, `EMAIL_PASSWORD_CALLBACK` is called before the page is returned.

The `EMAIL_MAIL_PAGE_TEMPLATE` is a template that receives `{{ success }}`(`bool`), `{{ user }}`(`Model`) and `{{ request }}`(`WSGIRequest`) as arguments,
it might look something like this:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Password Changed</title>
</head>
<body>
{% if success %}
{{ user.username }}, your password has been changed!
{% else %}
Error, invalid token!
{% endif %}
</body>
</html>
```

### Custom View Method

If you want to use your custom Django view for the verification of the token (if you need a more complex behaviour) you can do the following:

1. Add your view to the `urls.py` file, using the correct url argument
2. Mark your view using the corresponding decorator
3. Call the token verification function

Here is the code:

```python
# urls.py

from django.urls import path
from .views import confirm_view, password_view

urlpatterns = [
    ...
    path('email/<str:token>/', confirm_view), # remember to set the "token" parameter in the url!
    path('password/<str:token>/', password_view), # remember to set the "token" parameter in the url!
    ...
]
```

> **_IMPORTANT:_** the path must **NOT** have the `name` attribute set

```python
# views.py

from django.http import HttpResponse
from django_email_verification import verify_email, verify_password, verify_email_view, verify_password_view


@verify_email_view
def confirm_view(request, token):
    success, user = verify_email(token)
    return HttpResponse(f'Account verified, {user.username}' if success else 'Invalid token')


@verify_password_view
def password_view(request, token):
    if request.method == 'POST' and (pwd := request.POST.get('password')) is not None:
        success, user = verify_password(token, pwd)
        return HttpResponse(f'Password Changed, {user.username}' if success else 'Invalid token')
    return HttpResponse('Wrong Method')
```
The decorators allow the app to automatically generate a url with the correct link to the view, as long as there is only one view per decorator and it has the correct arguments.

The functions `verify_email(token)` and `verify_password(token, password)` verify the token and, if it is correct, call the corresponding callback (`EMAIL_MAIL_CALLBACK` and `EMAIL_PASSWORD_CALLBACK` respectively).

#### Manual Token Verification

If you only need to check the token, you can use the following code:
```python
from django_email_verification import default_token_generator

valid, user = default_token_generator.check_token(token, kind='MAIL')      # For an email token
valid, user = default_token_generator.check_token(token, kind='PASSWORD')  # For a password token
```

## Testing

If you are using django-email-verification and you want to test the email, if settings.DEBUG == True, then two items
will be added to the email headers.
You can obtain these by checking the django.core.mail outbox, which will have a non-zero length if an email has been
sent. Retrieve the email and obtain the link (includes token) or the token to use in your code.

```python
from django.core import mail

...
test body
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

(You will need [coverage](https://pypi.org/project/coverage/), [pytest](https://pypi.org/project/pytest/)
and [pytest-django](https://pypi.org/project/pytest-django/))

### Logo copyright:

Logo by <a href="https://github.com/filippoveggo" title="Flippo Veggo">Filippo Veggo</a>
<div>"Django and the Django logo are registered trademarks of Django Software Foundation.<br/>Usage of the Django trademarks are subject to the Django Trademark licensing Agreement."</div>
<div>Icons made by <a href="https://www.flaticon.com/authors/kiranshastry" title="Kiranshastry">Kiranshastry</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a></div>
<div>Icons made by <a href="https://www.flaticon.com/authors/pixel-perfect" title="Pixel perfect">Pixel perfect</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a></div>

[^1]: The `EMAIL_{MAIL|PASSWORD}_CALLBACK` can be a function on the `AUTH_USER_MODEL`, for example:
    ```python
    EMAIL_{MAIL|PASSWORD}_CALLBACK = get_user_model().callback
    ```
