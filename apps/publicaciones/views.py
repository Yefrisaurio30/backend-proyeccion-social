from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Prefetch, Q
from apps.imagenes.models import Imagen
from .models import Publicacion, Categoria
from .serializers import (
    PublicacionSerializer,
    PublicacionListSerializer,
    PublicacionPublicSerializer,
    CategoriaSerializer,
)
from .filters import PublicacionFilter, PublicacionPublicFilter
from apps.usuarios.permissions import es_staff


class EsStaffOSoloLectura(BasePermission):
    """Lectura pública; escritura solo para staff (S3)."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or es_staff(request.user)


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [EsStaffOSoloLectura]
    pagination_class = None


def queryset_con_metricas():
    """Conteos anotados + portada con prefetch: evita N+1 en listados (P1)."""
    return (
        Publicacion.objects.select_related('categoria', 'usuario')
        .annotate(
            imagenes_count=Count('imagenes', distinct=True),
            comentarios_count=Count(
                'comentarios',
                filter=Q(comentarios__estado='APROBADO'),
                distinct=True,
            ),
        )
        .prefetch_related(
            Prefetch('imagenes', queryset=Imagen.objects.order_by('fechaCarga'))
        )
    )


class PublicacionViewSet(viewsets.ModelViewSet):
    """
    Gestion de publicaciones.
    - Staff: acceso total (crear, editar, publicar, archivar, eliminar).
    - Usuario autenticado: crea propuestas (BORRADOR o EN_REVISION),
      y solo ve/edita/elimina las SUYAS. No puede publicar ni archivar.
    """
    queryset = Publicacion.objects.select_related('categoria', 'usuario').all()
    filterset_class = PublicacionFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['titulo', 'resumen', 'contenido']
    ordering_fields = ['fechaPublicacion', 'titulo', 'fechaCreacion']
    ordering = ['-fechaCreacion']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = queryset_con_metricas()
        if es_staff(self.request.user):
            return qs
        return qs.filter(usuario=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return PublicacionListSerializer
        return PublicacionSerializer

    def perform_create(self, serializer):
        user = self.request.user
        estado = serializer.validated_data.get('estado')
        if es_staff(user):
            serializer.save(usuario=user)
        else:
            if estado not in (Publicacion.Estado.BORRADOR, Publicacion.Estado.EN_REVISION):
                estado = Publicacion.Estado.EN_REVISION
            serializer.save(usuario=user, estado=estado)

    def perform_update(self, serializer):
        user = self.request.user
        if es_staff(user):
            serializer.save()
            return
        estado = serializer.validated_data.get('estado')
        if estado in (Publicacion.Estado.PUBLICADA, Publicacion.Estado.ARCHIVADA):
            raise PermissionDenied('Solo el administrador puede publicar o archivar.')
        # Lo ya publicado/archivado vuelve a revisión al editarse (L1).
        if serializer.instance.estado in (
            Publicacion.Estado.PUBLICADA, Publicacion.Estado.ARCHIVADA,
        ):
            serializer.save(estado=Publicacion.Estado.EN_REVISION)
            return
        serializer.save()

    @action(detail=True, methods=['post'], url_path='publicar')
    def publicar(self, request, pk=None):
        if not es_staff(request.user):
            raise PermissionDenied('Solo el administrador puede publicar.')
        publicacion = self.get_object()
        if publicacion.estado == Publicacion.Estado.PUBLICADA:
            return Response(
                {'detail': 'La publicacion ya esta publicada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        publicacion.publicar()
        return Response(
            {'detail': 'Publicacion publicada exitosamente.', 'estado': publicacion.estado},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='despublicar')
    def despublicar(self, request, pk=None):
        if not es_staff(request.user):
            raise PermissionDenied('Solo el administrador puede despublicar.')
        publicacion = self.get_object()
        if publicacion.estado not in (Publicacion.Estado.PUBLICADA, Publicacion.Estado.EN_REVISION):
            return Response(
                {'detail': 'Solo se pueden despublicar publicaciones PUBLICADAS o EN_REVISION.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        publicacion.despublicar()
        return Response(
            {'detail': 'Publicacion despublicada.', 'estado': publicacion.estado},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='archivar')
    def archivar(self, request, pk=None):
        if not es_staff(request.user):
            raise PermissionDenied('Solo el administrador puede archivar.')
        publicacion = self.get_object()
        try:
            publicacion.cambiar_estado(Publicacion.Estado.ARCHIVADA)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {'detail': 'Publicacion archivada.', 'estado': publicacion.estado},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='enviar-revision')
    def enviar_revision(self, request, pk=None):
        publicacion = self.get_object()
        if not es_staff(request.user):
            if publicacion.usuario_id != request.user.pk:
                raise PermissionDenied('Solo puedes enviar tus propias propuestas.')
            if publicacion.estado != Publicacion.Estado.BORRADOR:
                return Response(
                    {'detail': 'Solo se pueden enviar borradores a revisión.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if publicacion.estado == Publicacion.Estado.PUBLICADA:
            return Response(
                {'detail': 'La publicacion ya esta publicada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            publicacion.cambiar_estado(Publicacion.Estado.EN_REVISION)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {'detail': 'Publicacion enviada a revisión.', 'estado': publicacion.estado},
            status=status.HTTP_200_OK,
        )


class PublicacionPublicViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint publico. Retorna publicaciones PUBLICADA y ARCHIVADA
    (las archivadas se muestran como "Completado" en el portal).
    Staff autenticado puede previsualizar EN_REVISION/BORRADOR.
    Soporta busqueda, filtros por categoria y estado, y paginacion.
    """
    serializer_class = PublicacionPublicSerializer
    filterset_class = PublicacionPublicFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['titulo', 'resumen', 'contenido']
    ordering_fields = ['fechaPublicacion', 'titulo']
    ordering = ['-fechaPublicacion']

    def get_queryset(self):
        qs = queryset_con_metricas()
        if es_staff(self.request.user):
            return qs
        return qs.filter(estado__in=[Publicacion.Estado.PUBLICADA, Publicacion.Estado.ARCHIVADA])

    def get_serializer_class(self):
        if es_staff(self.request.user) and self.action == 'retrieve':
            return PublicacionSerializer
        return PublicacionPublicSerializer

    def retrieve(self, request, *args, **kwargs):
        from django.db.models import F
        from django.utils import timezone
        instance = self.get_object()
        # Solo contar vista si es publica; no inflar en preview staff.
        # Una vista por sesión y ventana de 1 hora (P4).
        if instance.estado in [Publicacion.Estado.PUBLICADA, Publicacion.Estado.ARCHIVADA]:
            clave = f'vista_pub_{instance.pk}'
            ultima = (request.session.get(clave) or 0)
            ahora = timezone.now().timestamp()
            if ahora - float(ultima) > 3600:
                Publicacion.objects.filter(pk=instance.pk).update(vistas=F('vistas') + 1)
                instance.refresh_from_db(fields=['vistas'])
                request.session[clave] = ahora
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
