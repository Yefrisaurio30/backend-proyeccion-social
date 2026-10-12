"""Desarrollo. Hereda de base.py (C1)."""
from config.settings.base import *  # noqa: F401, F403
from decouple import config, Csv

SECRET_KEY = config('SECRET_KEY', default='django-local-dev-key-not-for-production')
# Variables configurables por entorno también en desarrollo (C3).
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:5173,http://127.0.0.1:5173',
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

# Origenes confiables para CSRF (el navegador envia cabecera Origin en los POST).
# Sin esto Django rechaza el login con "CSRF Failed: Origin checking failed".
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:5173,http://127.0.0.1:5173',
).split(',')

AUTH_PASSWORD_VALIDATORS = []
