from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, BasePermission
from .models import Solicitud
from .serializers import (
    SolicitudCreateSerializer,
    SolicitudAdminSerializer,
    SolicitudEstadoSerializer,
)


class IsStaffUser(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


class PublicSolicitudCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SolicitudCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                'detail': 'Solicitud enviada correctamente. Le contactaremos pronto.',
                'id': serializer.data['id'],
            },
            status=status.HTTP_201_CREATED,
        )


class SolicitudViewSet(viewsets.ModelViewSet):
    serializer_class = SolicitudAdminSerializer
    permission_classes = [IsStaffUser]
    search_fields = ['nombre', 'email', 'asunto', 'mensaje']
    filterset_fields = ['estado', 'tipo']
    pagination_class = None

    def get_queryset(self):
        qs = Solicitud.objects.all()
        search = self.request.query_params.get('search', '').strip()
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(nombre__icontains=search)
                | Q(email__icontains=search)
                | Q(telefono__icontains=search)
                | Q(asunto__icontains=search)
                | Q(mensaje__icontains=search)
            )
        return qs

    def partial_update(self, request, *args, **kwargs):
        serializer = SolicitudEstadoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.get_object()
        instance.estado = serializer.validated_data['estado']
        instance.save(update_fields=['estado'])
        return Response(SolicitudAdminSerializer(instance).data)