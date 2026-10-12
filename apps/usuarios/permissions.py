from rest_framework.permissions import BasePermission


# Única lista de roles con privilegios de staff (L2). El frontend no la
# duplica: la API ya envía is_staff/is_superuser/roles/permisos.
ROLES_STAFF = frozenset([
    'Superadmin', 'Coordinación Central', 'Moderador', 'EditorPublicaciones',
])


def es_staff(user):
    """Única definición de 'staff' para todo el backend (L2)."""
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    return user.roles_rel.filter(rol__nombre__in=ROLES_STAFF).exists()


_es_staff = es_staff


class IsStaffOrHasRole(BasePermission):
    def has_permission(self, request, view):
        return es_staff(request.user)


def es_superadmin(user):
    """Superusuario o rol Superadmin. Uso: gestión de usuarios y roles (S1)."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.roles_rel.filter(rol__nombre='Superadmin').exists()


class SoloSuperadmin(BasePermission):
    def has_permission(self, request, view):
        return es_superadmin(request.user)
