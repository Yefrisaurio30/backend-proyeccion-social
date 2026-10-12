from rest_framework.permissions import BasePermission

from apps.usuarios.permissions import es_staff


class IsModeratorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return es_staff(request.user)
