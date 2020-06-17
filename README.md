# Django email validator


## Requirements
+ Python >= 3.8
+ Django 3.0.7

## General concept
![alt text](https://github.com/LeoneBacciu/django-email-verification/blob/master/emailFlow.png?raw=True "Flow")

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
    'django_email_verification', # you have to add this
]
```

## Settings parameters
You have to add these parameters to the settings, you have to include all of them except the last one:
```python
EMAIL_ACTIVE_FIELD = 'is_active'
EMAIL_SERVER = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_ADDRESS = 'mymail@gmail.com'
EMAIL_PASSWORD = 'mYC00lP4ssw0rd' # os.environ['password_key'] suggested
EMAIL_MAIL_SUBJECT = 'Confirm your email'
EMAIL_MAIL_HTML = 'mail_body.html'
EMAIL_MAIL_PLAIN = 'mail_body.txt'
EMAIL_PAGE_TEMPLATE = 'confirm_template.html'
EMAIL_PAGE_DOMAIN = 'http://mydomain.com/'
```
In detail:
+ `EMAIL_ACTIVE_FIELD`: the user model filed which will be set to `True` once the email is confirmed
+ `EMAIL_SERVER`: your mail provider's server (e.g. `'smtp.gmail.com'` for gmail)
+ `EMAIL_PORT`: your mail provider's server port (e.g. `587` for gmail)
+ `EMAIL_ADDRESS`: your email address
+ `EMAIL_PASSWORD`: your email address' password
+ `EMAIL_MAIL_`:
    * `SUBJECT`: the mail default subject (needed)
    * `HTML`: the mail body in form of html (not needed)
    * `PLAIN`: the mail body in form of .txt file (needed if `HTML` is not defined)
+ `EMAIL_PAGE_TEMPLATE`: the template of the success/error view
+ `EMAIL_PAGE_DOMAIN`: the domain of the confirmation link (usually your site's domain)

## Templates examples
The `EMAIL_MAIL_HTML` should look like this (`{{ link }}` is passed during the rendering):
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>
        h1{ color: blue; }
    </style>
</head>
    <body>
        <h1>You are almost there!</h1><br>
        <h2>Please click <a href="{{ link }}">here</a> to confirm your account</h2>
    </body>
</html>
```

The `EMAIL_MAIL_PLAIN` should look like this (`{{ link }}` is passed during the rendering):
```text
You are almost there!
Please click the following link to confirm your account
{{ link }}
```

The `EMAIL_PAGE_TEMPLATE` should look like this (`{{ success }}` is boolean and passed during the rendering):
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Confirmation</title>
    <style>
        body{ color: blue; }
    </style>
</head>
<body>
    {% if success %}
        You have confirmed your account!
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
from django_email_verification import sendConfirm

def myCreateView(request):
    ...
    user = get_user_model().objects.create(username=username, password=password, email=email)
    sendConfirm(user)
    return render(...)
```
`sendConfirm(user)` sets user's `is_active` to `False` and sends an email with the defined template (and the pseudo-random generated token) to the user.

## Token verification
You have to include the urls in `urls.py`
```python
from django.contrib import admin
from django.urls import path, include
from django_email_verification import urls as mail_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    ...
    path('email/', include(mail_urls)),
]
```
When a request arrives to `https.//mydomain.com/email/<base64 email>/<token>` the package verifies the token and:
+ if it corresponds to a pending token it renders the `EMAIL_PAGE_TEMPLATE` passing `success=True` and deletes the token
+ if it doesn't correspond it renders the `EMAIL_PAGE_TEMPLATE` passing `success=False`