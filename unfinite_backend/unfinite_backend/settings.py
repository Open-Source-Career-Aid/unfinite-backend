"""
Django settings for unfinite_backend project.

Generated by 'django-admin startproject' using Django 4.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
from dotenv import load_dotenv
import os, openai
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_ROOT= BASE_DIR / 'static/'
#print(STATIC_ROOT)

# STATICFILES_DIRS = [BASE_DIR / 'unfinitefront/unfinitebeta/build/static', BASE_DIR / 'unfinitefront/unfinitebeta/build/']
#print(STATICFILE_DIRS)
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = str(os.getenv('SECRET_KEY'))
#SERPHOUSE_KEY = str(os.getenv('SCRAPING_KEY'))
SCRAPING_KEY = str(os.getenv('SCRAPING_KEY'))

# key for authentication between api and queryhandler
QUERYHANDLER_KEY = str(os.getenv('QUERYHANDLER_KEY'))
QUERYHANDLER_URL = str(os.getenv('QUERYHANDLER_URL'))


DOCHANDLER_URL = str(os.getenv('DOCHANDLER_URL'))

# get openai api key
OPENAI_API_KEY = str(os.getenv('OPENAI_API_KEY'))

PINECONE_KEY = str(os.getenv('PINECONE_KEY'))

PINECONE_ENV = str(os.getenv('PINECONE_ENV'))
PINECONE_INDEX_NAME = str(os.getenv('PINECONE_INDEX_NAME'))
MODEL_SERVER_URL = str(os.getenv('MODEL_SERVER_URL'))
MODEL_SERVER_KEY = str(os.getenv('MODEL_SERVER_KEY'))

# CORS
CORS_ALLOW_CREDENTIALS = True
#CORS_ORIGIN_WHITELIST = ['http://localhost:3000', '3.135.226.130'] # For development of the front-end. Will be https://app.unfinite.co

# NOTE: hopefully default cache is fine for django-ratelimit?

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

IS_PRODUCTION = False

ALLOWED_HOSTS = ['app.unfinite.co', 'localhost', '3.19.61.62', '127.0.0.1', '3.135.226.130']

#CSRF_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_HTTPONLY = False  # if frontend served seperately, this is True
# SESSION_COOKIE_HTTPONLY = True

#CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"
CORS_ORIGIN_WHITELIST = ['http://localhost:3000']
CSRF_TRUSTED_ORIGINS = ['https://app.unfinite.co', 'http://localhost:3000'] # For dev. prod: https://app.unfinite.co

# Enable for production, forces HTTPS for cookies:
# CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = not DEBUG


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders', # For CORS stuff
    'api',
    'queryhandler',
    'import_export',
    'dochandler'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'corsheaders.middleware.CorsMiddleware', # CORS stuff
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'unfinite_backend.urls'

t = []
if os.getenv("REACT_DIR") is not None:
    t = [BASE_DIR / os.getenv("REACT_DIR")]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': t,
        'APP_DIRS': True,
        'OPTIONS': {
            #'sql_mode': 'traditional',
            #'isolation_level': 'read committed',
            #'charset': 'utf8mb4',
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'unfinite_backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
	#'USER': os.getenv('DB_USER'),
	#'PASSWORD': os.getenv('DB_PASSWORD'), #put this stuff in .env
	#'HOST': os.getenv('DB_HOST'),
	#'PORT': '3306',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AUTH_USER_MODEL = 'api.UnfiniteUser'

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
