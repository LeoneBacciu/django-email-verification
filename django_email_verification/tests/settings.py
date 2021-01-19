import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'i6)fwiz^ru7hj^gzk4t=i9la-gi6)s4++4um6+drg^m(g-5c_x'

DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django_email_verification',
]

ROOT_URLCONF = 'django_email_verification.tests.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'tests/templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


def verified(user):
    user.is_active = True


EMAIL_VERIFIED_CALLBACK = verified
EMAIL_FROM_ADDRESS = 'rousseau.platform@gmail.com'
EMAIL_MAIL_SUBJECT = 'Conferma la tua mail'
EMAIL_MAIL_HTML = 'mail.html'
EMAIL_MAIL_PLAIN = 'plainmail.txt'
EMAIL_TOKEN_LIFE = 60 * 60
EMAIL_PAGE_TEMPLATE = 'confirm.html'
EMAIL_PAGE_DOMAIN = 'https://test.com/'
