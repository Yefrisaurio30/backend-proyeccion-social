"""Producción. Hereda de base.py, NO de local.py (C1)."""
from config.settings.base import *  # noqa: F401, F403

import os

from django.core.exceptions import ImproperlyConfigured

# ======================================================================
# PRODUCTION SETTINGS - Sistema de Proyeccion Social UNIMINUTO
# ======================================================================

DEBUG = False

# En producción la clave es obligatoria: fallar sin ella (S5).
SECRET_KEY = os.environ['SECRET_KEY']
if SECRET_KEY.startswith('django-insecure') or len(SECRET_KEY) < 40:
    raise ImproperlyConfigured('SECRET_KEY de producción inválida')

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()
]

# ------------------------------------------------------------------
# CORS - Politicas estrictas
# ------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True
# Origenes confiables para CSRF (requerido para login con sesion desde el frontend)
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', os.environ.get('CORS_ALLOWED_ORIGINS', '')).split(',')
    if origin.strip()
]
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ------------------------------------------------------------------
# Seguridad HTTPS (Render / Railway)
# ------------------------------------------------------------------
# El TLS termina en el proxy (Render/Railway/nginx): sin esto, Django cree
# que todo llega por HTTP y SECURE_SSL_REDIRECT entra en bucle (C2).
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ------------------------------------------------------------------
# WhiteNoise - Archivos estaticos
# ------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.actividad.middleware.ActividadUsuarioMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# STORAGES reemplaza a STATICFILES_STORAGE (obsoleto desde Django 4.2).
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
STATIC_ROOT = BASE_DIR / 'staticfiles'  # noqa: F405

# ------------------------------------------------------------------
# Base de datos - PostgreSQL (Supabase / Render)
# ------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'proyeccion_social'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
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
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# ------------------------------------------------------------------
# Contraseñas: no heredar la lista vacía de local.py (S6).
# ------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
