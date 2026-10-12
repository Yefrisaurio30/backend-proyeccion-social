"""Guarda el usuario del request para que las señales auditen al actor real (L3).

Sin dependencias nuevas: contextvars + middleware. Fuera de un request
(shell, seed) las señales usan el autor del objeto como antes.
"""
from contextvars import ContextVar

_usuario_actual = ContextVar('actividad_usuario_actual', default=None)


def get_current_user():
    """Usuario autenticado del request en curso, o None."""
    usuario = _usuario_actual.get()
    if usuario is not None and getattr(usuario, 'is_authenticated', False):
        return usuario
    return None


class ActividadUsuarioMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = getattr(request, 'user', None)
        token = _usuario_actual.set(
            usuario if getattr(usuario, 'is_authenticated', False) else None
        )
        try:
            return self.get_response(request)
        finally:
            _usuario_actual.reset(token)
