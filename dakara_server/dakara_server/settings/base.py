"""
Django base settings for the Dakara server project.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/

This file should not be modified if you are not a dev.
"""

import os

from dakara_server.version import __version__ as VERSION, __date__ as DATE  # noqa F401


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Application definition

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'django.contrib.sites',
    "channels",
    "ordered_model",
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    "rest_framework",
    "rest_framework.authtoken",
    "dj_rest_auth",
    'dj_rest_auth.registration',
    "library",
    "playlist.apps.PlaylistConfig",
    "users",
    "internal.apps.InternalConfig",
)

MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

# user model

AUTH_USER_MODEL = "users.DakaraUser"

# channels

ASGI_APPLICATION = "dakara_server.routing.application"

# urls

ROOT_URLCONF = "dakara_server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "TIMEOUT": None,
    }
}

WSGI_APPLICATION = "dakara_server.wsgi.application"


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = "/static/"

STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

# Django REST config
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "internal.pagination.PageNumberPaginationCustom",
    "PAGE_SIZE": 10,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

# Needed for dj-rest-auth
SITE_ID = 1

REST_AUTH_SERIALIZERS = {
    "LOGIN_SERIALIZER": "users.serializers.DakaraLoginSerializer"
}

# All-auth config
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_AUTHENTICATION_METHOD = "username_email"

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Mail config
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
