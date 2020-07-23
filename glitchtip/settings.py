"""
Django settings for glitchtip project.

Generated by 'django-admin startproject' using Django 3.0rc1.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import os
import sys
import warnings
import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from celery.schedules import crontab

env = environ.Env(
    ALLOWED_HOSTS=(list, ["*"]),
    DEBUG=(bool, False),
    DEBUG_TOOLBAR=(bool, False),
    AWS_ACCESS_KEY_ID=(str, None),
    AWS_SECRET_ACCESS_KEY=(str, None),
    AWS_STORAGE_BUCKET_NAME=(str, None),
    AWS_S3_ENDPOINT_URL=(str, None),
    AWS_LOCATION=(str, None),
    STATIC_URL=(str, "/"),
    STATICFILES_STORAGE=(
        str,
        "whitenoise.storage.CompressedManifestStaticFilesStorage",
    ),
)
path = environ.Path()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

# Enable only for running end to end testing. Debug must be True to use.
ENABLE_TEST_API = env.bool("ENABLE_TEST_API", False)
if DEBUG is False:
    ENABLE_TEST_API = False

ALLOWED_HOSTS = env("ALLOWED_HOSTS")
# Necessary for kubernetes health checks
POD_IP = env.str("POD_IP", default=None)
if POD_IP:
    ALLOWED_HOSTS.append(POD_IP)

# Used in email and DSN generation. Set to full domain such as https://glitchtip.example.com
GLITCHTIP_DOMAIN = env.url("GLITCHTIP_DOMAIN", default="http://localhost:8000")

# Events and associated data older than this will be deleted from the database
GLITCHTIP_MAX_EVENT_LIFE_DAYS = env.int("GLITCHTIP_MAX_EVENT_LIFE_DAYS", default=90)

# For development purposes only, prints out inbound event store json
EVENT_STORE_DEBUG = env.bool("EVENT_STORE_DEBUG", False)


# GlitchTip can track GlitchTip's own errors.
# If enabling this, use a different server to avoid infinite loops.
def before_send(event, hint):
    """Don't log django.DisallowedHost errors in Sentry."""
    if "log_record" in hint:
        if hint["log_record"].name == "django.security.DisallowedHost":
            return None

    return event


SENTRY_DSN = env.str("SENTRY_DSN", None)
# Optionally allow a different DSN for the frontend
SENTRY_FRONTEND_DSN = env.str("SENTRY_FRONTEND_DSN", SENTRY_DSN)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN, integrations=[DjangoIntegration()], before_send=before_send,
    )


def show_toolbar(request):
    return env("DEBUG_TOOLBAR")


DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": show_toolbar}
DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.postgres",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.gitlab",
    "allauth.socialaccount.providers.github",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.microsoft",
    "anymail",
    "corsheaders",
    "django_celery_results",
    "django_filters",
    "debug_toolbar",
    "rest_framework",
    "drf_yasg",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "storages",
    "glitchtip",
    "alerts",
    "organizations_ext",
    "event_store",
    "issues",
    "users",
    "projects",
    "teams",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "csp.middleware.CSPMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "glitchtip.middleware.proxy.DecompressBodyMiddleware",
]

ROOT_URLCONF = "glitchtip.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [path("dist"), path("templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "glitchtip.wsgi.application"

CORS_ORIGIN_ALLOW_ALL = env.bool("CORS_ORIGIN_ALLOW_ALL", True)
CORS_ORIGIN_WHITELIST = env.tuple("CORS_ORIGIN_WHITELIST", str, default=())
SECURE_BROWSER_XSS_FILTER = True
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"]
CSP_STYLE_SRC_ELEM = ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"]
CSP_FONT_SRC = ["'self'", "https://fonts.gstatic.com"]
# Redoc requires blob
CSP_WORKER_SRC = ["'self'", "blob:"]
# GlitchTip can record it's own errors
CSP_CONNECT_SRC = ["'self'", "https://app.glitchtip.com"]
# Needed for Matomo and Stripe for SaaS use cases. Both are disabled by default.
CSP_SCRIPT_SRC = ["'self'", "https://matomo.glitchtip.com", "https://js.stripe.com"]
CSP_IMG_SRC = ["'self'", "https://matomo.glitchtip.com"]
CSP_FRAME_SRC = ["'self'", "https://js.stripe.com"]
# Consider tracking CSP reports with GlitchTip itself
CSP_REPORT_URI = env.tuple("CSP_REPORT_URI", str, None)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", 0)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", False)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", False)
SESSION_COOKIE_SAMESITE = env.str("SESSION_COOKIE_SAMESITE", "Lax")

ENVIRONMENT = env.str("ENVIRONMENT", None)
GLITCHTIP_VERSION = env.str("GLITCHTIP_VERSION", "dev")

DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", "webmaster@localhost")
ANYMAIL = {
    "MAILGUN_API_KEY": env.str("MAILGUN_API_KEY", None),
    "MAILGUN_SENDER_DOMAIN": env.str("MAILGUN_SENDER_DOMAIN", None),
}

ACCOUNT_EMAIL_SUBJECT_PREFIX = ""

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    "default": env.db(default="postgres://postgres:postgres@postgres:5432/postgres")
}

# We need to support both url and broken out host to support helm redis chart
REDIS_HOST = env.str("REDIS_HOST", None)
if REDIS_HOST:
    REDIS_PORT = env.str("REDIS_PORT", "6379")
    REDIS_DATABASE = env.str("REDIS_DATABASE", "0")
    REDIS_PASSWORD = env.str("REDIS_PASSWORD", None)
    if REDIS_PASSWORD:
        REDIS_URL = (
            f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DATABASE}"
        )
    else:
        REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DATABASE}"
else:
    REDIS_URL = env.str("REDIS_URL", "redis://redis:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "fanout_prefix": True,
    "fanout_patterns": True,
}
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"
CELERY_BEAT_SCHEDULE = {
    "send-alert-notifications": {
        "task": "alerts.tasks.process_alerts",
        "schedule": 60,
    },
    "cleanup-old-events": {
        "task": "issues.tasks.cleanup_old_events",
        "schedule": crontab(hour=6),
    },
    "set-organization-throttle": {
        "task": "organizations_ext.tasks.set_organization_throttle",
        "schedule": crontab(hour=7),
    },
}
CACHES = {"default": {"BACKEND": "redis_cache.RedisCache", "LOCATION": REDIS_URL}}

# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

SITE_ID = 1

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/
if DEBUG:
    STATIC_URL = "/static/"
else:  # This is needed for angular cli
    STATIC_URL = "/"


AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL")
AWS_LOCATION = env("AWS_LOCATION")

STATICFILES_DIRS = [
    "assets",
    "dist",
]
STATIC_ROOT = path("static/")
STATICFILES_STORAGE = env("STATICFILES_STORAGE")
EMAIL_BACKEND = env.str(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)

AUTH_USER_MODEL = "users.User"
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
INVITATION_BACKEND = "organizations_ext.invitation_backend.InvitationBackend"

OLD_PASSWORD_FIELD_ENABLED = True
LOGOUT_ON_PASSWORD_CHANGE = False

REST_AUTH_SERIALIZERS = {
    "USER_DETAILS_SERIALIZER": "users.serializers.UserSerializer",
    "TOKEN_SERIALIZER": "users.serializers.NoopTokenSerializer",
    "PASSWORD_RESET_SERIALIZER": "users.serializers.PasswordSetResetSerializer",
}
REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": "users.serializers.RegisterSerializer",
}
REST_AUTH_TOKEN_CREATOR = "users.utils.noop_token_creator"

# By default (False) only the first user may register and create an organization
# Other users must be invited. Intended for private instances
ENABLE_OPEN_USER_REGISTRATION = env.bool("ENABLE_OPEN_USER_REGISTRATION", False)

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

DEFAULT_RENDERER_CLASSES = ("rest_framework.renderers.JSONRenderer",)
if DEBUG:
    DEFAULT_RENDERER_CLASSES = DEFAULT_RENDERER_CLASSES + (
        "rest_framework.renderers.BrowsableAPIRenderer",
    )

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated",],
    "DEFAULT_PAGINATION_CLASS": "glitchtip.pagination.LinkHeaderPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_RENDERER_CLASSES": DEFAULT_RENDERER_CLASSES,
}

DRF_YASG_EXCLUDE_VIEWS = [
    "dj_rest_auth.registration.views.SocialAccountDisconnectView",
]
SWAGGER_SETTINGS = {
    "DEFAULT_AUTO_SCHEMA_CLASS": "glitchtip.yasg.SquadSwaggerAutoSchema",
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"null": {"class": "logging.NullHandler",},},
    "loggers": {
        "django.security.DisallowedHost": {"handlers": ["null"], "propagate": False,},
    },
}


def organization_request_callback(request):
    """ Gets an organization instance from the id passed through ``request``"""
    user = request.user
    if user:
        return user.organizations_ext_organization.filter(
            owner__organization_user__user=user
        ).first()


# Set to track activity with Matomo
MATOMO_URL = env.str("MATOMO_URL", default=None)
MATOMO_SITE_ID = env.str("MATOMO_SITE_ID", default=None)

# Is running unit test
TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

# Max events per month for free tier
BILLING_FREE_TIER_EVENTS = env.int("BILLING_FREE_TIER_EVENTS", 1000)
DJSTRIPE_SUBSCRIBER_MODEL = "organizations_ext.Organization"
DJSTRIPE_SUBSCRIBER_MODEL_REQUEST_CALLBACK = organization_request_callback
DJSTRIPE_USE_NATIVE_JSONFIELD = True
BILLING_ENABLED = False
STRIPE_LIVE_MODE = env.bool("STRIPE_LIVE_MODE", False)
if env.str("STRIPE_TEST_PUBLIC_KEY", None) or env.str("STRIPE_LIVE_PUBLIC_KEY", None):
    BILLING_ENABLED = True
    INSTALLED_APPS.append("djstripe")
    INSTALLED_APPS.append("djstripe_ext")
    STRIPE_TEST_PUBLIC_KEY = env.str("STRIPE_TEST_PUBLIC_KEY", None)
    STRIPE_TEST_SECRET_KEY = env.str("STRIPE_TEST_SECRET_KEY", None)
    STRIPE_LIVE_PUBLIC_KEY = env.str("STRIPE_LIVE_PUBLIC_KEY", None)
    STRIPE_LIVE_SECRET_KEY = env.str("STRIPE_LIVE_SECRET_KEY", None)
    DJSTRIPE_WEBHOOK_SECRET = env.str("DJSTRIPE_WEBHOOK_SECRET", None)
elif TESTING:
    # Must run tests with djstripe enabled
    BILLING_ENABLED = True
    INSTALLED_APPS.append("djstripe")
    INSTALLED_APPS.append("djstripe_ext")
    STRIPE_TEST_PUBLIC_KEY = "fake"
    STRIPE_TEST_SECRET_KEY = "sk_test_fake"  # nosec
    DJSTRIPE_WEBHOOK_SECRET = "whsec_fake"  # nosec

if TESTING:
    CELERY_TASK_ALWAYS_EAGER = True
    STATICFILES_STORAGE = None
    # https://github.com/evansd/whitenoise/issues/215
    warnings.filterwarnings(
        "ignore", message="No directory at", module="whitenoise.base"
    )
