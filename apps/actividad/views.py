from rest_framework import viewsets
from rest_framework.permissions import BasePermission
from apps.usuarios.permissions import es_staff
from .models import RegistroActividad
from .serializers import RegistroActividadSerializer


class IsStaffUser(BasePermission):
    def has_permission(self, request, view):
        return es_staff(request.user)


class RegistroActividadViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RegistroActividad.objects.select_related('usuario').all()
    serializer_class = RegistroActividadSerializer
    permission_classes = [IsStaffUser]
    # Paginación por defecto (P2): el registro crece sin parar.
