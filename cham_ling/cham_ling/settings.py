"""
Настройки Django для проекта ChamLing.

Этот модуль содержит все конфигурационные настройки приложения:
- Безопасность (SECRET_KEY, DEBUG)
- База данных (SQLite для разработки, PostgreSQL для продакшена)
- REST Framework настройки
- CORS настройки для работы с фронтендом
- JWT токены настройки
"""
from pathlib import Path
from decouple import config
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Разрешённые хосты для приёма запросов
# В продакшене указать конкретные домены!
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'api',  # Наше приложение с API
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cham_ling.urls'

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

WSGI_APPLICATION = 'cham_ling.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
if 'RDS_HOSTNAME' in os.environ:
    # Настройки для AWS Elastic Beanstalk с RDS PostgreSQL
    # Переменные окружения устанавливаются автоматически EB при подключении RDS
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'PASSWORD': os.environ['RDS_PASSWORD'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
        }
    }
else:
    # Настройки для локальной разработки с SQLite
    # SQLite файл хранится в корне проекта (db.sqlite3)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators
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

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Для collectstatic в продакшене

# Media files (загружаемые пользователями)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Кастомная модель пользователя (расширенная с полем balance)
AUTH_USER_MODEL = 'api.User'

# REST Framework настройки
# Используется JWT аутентификация для всех API endpoints
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# CORS настройки для работы с фронтендом
# Разрешаем запросы с фронтенда (React на localhost:3000)
CORS_ALLOWED_ORIGINS_STR = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000'
)
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in CORS_ALLOWED_ORIGINS_STR.split(',') if origin.strip()
]

# Разрешить все источники в режиме разработки (НЕ использовать в продакшене!)
# В продакшене использовать CORS_ALLOWED_ORIGINS с конкретными доменами
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

# Unsplash API ключ для автоматического подбора изображений
# Получить ключ можно на https://unsplash.com/developers
UNSPLASH_API_KEY = config('UNSPLASH_API_KEY', default='')

# JWT токены настройки
# ACCESS_TOKEN_LIFETIME: Время жизни access токена (60 минут)
# REFRESH_TOKEN_LIFETIME: Время жизни refresh токена (1 день)
# ROTATE_REFRESH_TOKENS: Автоматическая ротация refresh токенов при использовании
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
}

# Настройки аутентификации
# EmailAuthBackend: Позволяет логиниться по email вместо username
# ModelBackend: Стандартная Django аутентификация по username
AUTHENTICATION_BACKENDS = [
    'api.backends.EmailAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]