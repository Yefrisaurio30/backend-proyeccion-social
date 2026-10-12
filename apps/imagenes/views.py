from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from .models import Imagen
from .serializers import ImagenSerializer, ImagenUploadSerializer
from apps.usuarios.permissions import es_staff


ESTADOS_VISIBLES = ['PUBLICADA', 'ARCHIVADA']


class ImagenViewSet(viewsets.ModelViewSet):
    queryset = Imagen.objects.select_related('publicacion').all()
    serializer_class = ImagenSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = Imagen.objects.select_related('publicacion').all()
        user = self.request.user
        if es_staff(user):
            return qs
        # En escritura solo las publicaciones propias (S2): así un
        # DELETE/PATCH sobre imágenes ajenas devuelve 404.
        if self.action in ('update', 'partial_update', 'destroy'):
            if not user.is_authenticated:
                return qs.none()
            return qs.filter(publicacion__usuario=user)
        if user.is_authenticated:
            return qs.filter(
                Q(publicacion__usuario=user)
                | Q(publicacion__estado__in=ESTADOS_VISIBLES)
            )
        return qs.filter(publicacion__estado__in=ESTADOS_VISIBLES)

    def get_serializer_class(self):
        if self.action == 'create':
            return ImagenUploadSerializer
        return ImagenSerializer

    def perform_create(self, serializer):
        user = self.request.user
        publicacion = serializer.validated_data['publicacion']
        if not es_staff(user) and publicacion.usuario_id != user.pk:
            raise PermissionDenied('Solo puedes subir imágenes a tus propias publicaciones.')
        serializer.save()

    def perform_update(self, serializer):
        # La imagen no se puede mover a otra publicación (S2).
        if 'publicacion' in serializer.validated_data:
            raise PermissionDenied('No puedes mover una imagen a otra publicación.')
        serializer.save()

    def perform_destroy(self, instance):
        from .utils.storage import eliminar_imagen
        eliminar_imagen(instance.ruta)
        instance.delete()

    def create(self, request, *args, **kwargs):
        from .utils.storage import StorageError
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except StorageError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        imagen = serializer.instance
        return Response(
            ImagenSerializer(imagen).data,
            status=status.HTTP_201_CREATED,
        )