from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.db.models import Q
from .models import Comentario
from .serializers import (
    ComentarioCreateSerializer,
    ComentarioPublicSerializer,
    ComentarioModerationSerializer,
    ComentarioRechazarSerializer,
)
from .permissions import IsModeratorOrAdmin


class ComentarioViewSet(viewsets.ModelViewSet):
    """
    API de comentarios.
    - POST /api/comentarios/           : Crear comentario (auth required, estado=PENDIENTE)
    - GET  /api/comentarios/publicos/  : Comentarios aprobados de una publicacion
    - GET  /api/comentarios/pendientes/: Cola de moderacion (staff/superuser)
    - GET  /api/comentarios/           : Todos los comentarios (staff/superuser)
    - PATCH /api/comentarios/{id}/aprobar/
    - PATCH /api/comentarios/{id}/rechazar/
    """
    filterset_fields = ['estado', 'publicacion']
    search_fields = ['contenido', 'usuario__username']

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return Comentario.objects.select_related(
                'publicacion', 'usuario'
            ).all()
        return Comentario.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return ComentarioCreateSerializer
        if self.action == 'publicos':
            return ComentarioPublicSerializer
        if self.action in ('aprobar', 'rechazar'):
            return ComentarioRechazarSerializer
        return ComentarioModerationSerializer

    def get_permissions(self):
        if self.action in ('publicos',):
            return [AllowAny()]
        if self.action in ('create',):
            return [IsAuthenticated()]
        if self.action in ('list', 'retrieve', 'pendientes', 'aprobar', 'rechazar'):
            return [IsModeratorOrAdmin()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @action(detail=False, methods=['get'], url_path='publicos')
    def publicos(self, request):
        publicacion_id = request.query_params.get('publicacion_id')
        if not publicacion_id:
            return Response(
                {'detail': 'El parametro publicacion_id es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        comentarios = Comentario.objects.filter(
            publicacion_id=publicacion_id,
            estado=Comentario.Estado.APROBADO,
        ).select_related('usuario').order_by('-fechaCreacion')
        serializer = ComentarioPublicSerializer(comentarios, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='pendientes')
    def pendientes(self, request):
        comentarios = Comentario.objects.filter(
            estado=Comentario.Estado.PENDIENTE,
        ).select_related('publicacion', 'usuario').order_by('fechaCreacion')
        serializer = ComentarioModerationSerializer(comentarios, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='aprobar')
    def aprobar(self, request, pk=None):
        comentario = self.get_object()
        if comentario.estado != Comentario.Estado.PENDIENTE:
            return Response(
                {'detail': 'Solo se pueden aprobar comentarios pendientes.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        comentario.aprobar()
        return Response(
            {
                'detail': 'Comentario aprobado.',
                'estado': comentario.estado,
                'fechaModeracion': comentario.fechaModeracion,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['patch'], url_path='rechazar')
    def rechazar(self, request, pk=None):
        comentario = self.get_object()
        if comentario.estado != Comentario.Estado.PENDIENTE:
            return Response(
                {'detail': 'Solo se pueden rechazar comentarios pendientes.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ComentarioRechazarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        motivo = serializer.validated_data.get('motivo', '')
        comentario.rechazar(motivo=motivo)
        return Response(
            {
                'detail': 'Comentario rechazado.',
                'estado': comentario.estado,
                'fechaModeracion': comentario.fechaModeracion,
            },
            status=status.HTTP_200_OK,
        )
