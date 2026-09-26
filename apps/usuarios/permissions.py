from rest_framework.permissions import BasePermission


def _es_staff(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    return user.roles_rel.filter(rol__nombre__in=[
        'Superadmin', 'Coordinación Central', 'Moderador', 'EditorPublicaciones'
    ]).exists()


class IsStaffOrHasRole(BasePermission):
    def has_permission(self, request, view):
        return _es_staff(request.user)
