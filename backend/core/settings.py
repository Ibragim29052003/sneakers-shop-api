# настройки django для проекта core
import os
import sys
from pathlib import Path
from datetime import timedelta

try:
    import sentry_sdk
except ImportError:  # pragma: no cover
    sentry_sdk = None
from django.core.exceptions import ImproperlyConfigured

# сборка путей внутри проекта: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    """Читает bool-переменную окружения с безопасным fallback."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


# предупреждение безопасности: не запускайте с включенным отладчиком в продакшене!
DEBUG = env_bool('DJANGO_DEBUG', False)
ENABLE_SILK = env_bool('DJANGO_ENABLE_SILK', False)
TESTING = 'test' in sys.argv

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-dev-key'
    else:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY must be set when DEBUG is False.')

ALLOWED_HOSTS = [host.strip() for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if host.strip()]
if DEBUG and not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# определение приложения
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # сторонние приложения
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'django_filters',
    'import_export',
    'simple_history',
    'corsheaders',
    'django_celery_beat',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    
    # локальные приложения
    'users',
    'products',
    'orders',
    'reviews',
    'carts',
    'suppliers',
]

if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')

if ENABLE_SILK:
    INSTALLED_APPS.append('silk')

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

if DEBUG:
    MIDDLEWARE.insert(2, 'debug_toolbar.middleware.DebugToolbarMiddleware')

if ENABLE_SILK:
    MIDDLEWARE.insert(2, 'silk.middleware.SilkyMiddleware')

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'

SENTRY_DSN = os.environ.get('SENTRY_DSN', '').strip()
if SENTRY_DSN and sentry_sdk is not None:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=True,
        traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
        profiles_sample_rate=float(os.environ.get('SENTRY_PROFILES_SAMPLE_RATE', '0.0')),
    )

# база данных
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
db_host = os.environ.get('POSTGRES_HOST', 'localhost')
if db_host == 'postgres' and not Path('/.dockerenv').exists():
    # Удобный fallback для локального запуска без Docker.
    db_host = 'localhost'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'onlinestore'),
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        'HOST': db_host,
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# проверка пароля
AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# интернационализация
LANGUAGE_CODE = 'ru'
TIME_ZONE = os.environ.get('CELERY_TIMEZONE', 'UTC')
USE_I18N = True
USE_TZ = True

# статические файлы (css, javascript, изображения)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'products' / 'static',
]

# медиа файлы (загрузки)
# MEDIA_URL - URL по которому будут доступны загруженные файлы
# MEDIA_ROOT - физическая директория для хранения файлов
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# тип поля первичного ключа по умолчанию
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# настройки django rest framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.environ.get('DRF_THROTTLE_ANON', '120/hour'),
        'user': os.environ.get('DRF_THROTTLE_USER', '1000/hour'),
        'auth_login': os.environ.get('DRF_THROTTLE_AUTH_LOGIN', '20/minute'),
        'auth_register': os.environ.get('DRF_THROTTLE_AUTH_REGISTER', '10/minute'),
        'social_auth': os.environ.get('DRF_THROTTLE_SOCIAL_AUTH', '20/minute'),
        'supplier_registration': os.environ.get('DRF_THROTTLE_SUPPLIER_REGISTRATION', '5/minute'),
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# настройки django simple jwt
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

SITE_ID = int(os.environ.get('DJANGO_SITE_ID', '1'))
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)
# django-allauth (новый формат настроек без deprecated полей)
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '').strip()
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '').strip()
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    SOCIALACCOUNT_PROVIDERS = {
        'google': {
            'APP': {
                'client_id': GOOGLE_CLIENT_ID,
                'secret': GOOGLE_CLIENT_SECRET,
                'key': '',
            },
            'SCOPE': ['profile', 'email'],
            'AUTH_PARAMS': {'access_type': 'online'},
        }
    }

# Email / Mailhog
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'mailhog')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '1025'))
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@onlinestore.local')

# Celery
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_TIMEZONE = os.environ.get('CELERY_TIMEZONE', TIME_ZONE)
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

if TESTING:
    # В тестах не требуем внешний Redis: задачи выполняются синхронно в процессе.
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_TASK_IGNORE_RESULT = True

# настройки cors
CORS_ALLOW_ALL_ORIGINS = DEBUG
if not DEBUG:
    CORS_ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
        if origin.strip()
    ]

# security hardening
SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', False)
SESSION_COOKIE_SECURE = env_bool('DJANGO_SESSION_COOKIE_SECURE', not DEBUG)
CSRF_COOKIE_SECURE = env_bool('DJANGO_CSRF_COOKIE_SECURE', not DEBUG)
SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', False)
SECURE_HSTS_PRELOAD = env_bool('DJANGO_SECURE_HSTS_PRELOAD', False)
SECURE_CONTENT_TYPE_NOSNIFF = env_bool('DJANGO_SECURE_CONTENT_TYPE_NOSNIFF', True)
SECURE_REFERRER_POLICY = os.environ.get('DJANGO_SECURE_REFERRER_POLICY', 'same-origin')
X_FRAME_OPTIONS = os.environ.get('DJANGO_X_FRAME_OPTIONS', 'DENY')

if env_bool('DJANGO_USE_X_FORWARDED_PROTO', False):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# кэширование
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 минут
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

# логирование
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
