"""
Selector de configuracion de Django.

Al existir este paquete, Python lo resuelve ANTES que el modulo
`config/settings.py`, asi que `DJANGO_SETTINGS_MODULE=config.settings`
(el valor por defecto en manage.py y wsgi.py) siempre cae aqui.
Por eso este archivo debe ser el punto de entrada, no uno vacio.

La variante concreta se elige con DJANGO_SETTINGS_ENV:
    local  -> config.settings.local  (desarrollo, DEBUG=True)
    prod   -> config.settings.prod   (produccion, DEBUG=False)
"""

import os

_SETTINGS_ENV = os.environ.get('DJANGO_SETTINGS_ENV', 'local').strip().lower()

if _SETTINGS_ENV in ('prod', 'production'):
    from config.settings.prod import *  # noqa: F401,F403
else:
    from config.settings.local import *  # noqa: F401,F403
