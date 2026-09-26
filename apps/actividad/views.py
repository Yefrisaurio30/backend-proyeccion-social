from rest_framework import viewsets
from rest_framework.permissions import BasePermission
from .models import RegistroActividad
from .serializers import RegistroActividadSerializer


class IsStaffUser(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


class RegistroActividadViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RegistroActividad.objects.select_related('usuario').all()
    serializer_class = RegistroActividadSerializer
    permission_classes = [IsStaffUser]
    pagination_class = None
