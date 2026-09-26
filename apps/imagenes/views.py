from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied
from .models import Imagen
from .serializers import ImagenSerializer, ImagenUploadSerializer


def es_staff(user):
    return (
        user.is_authenticated and (user.is_staff or user.is_superuser)
    )


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

    def perform_destroy(self, instance):
        from .utils.storage import eliminar_imagen
        eliminar_imagen(instance.ruta)
        instance.delete()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        imagen = serializer.instance
        return Response(
            ImagenSerializer(imagen).data,
            status=status.HTTP_201_CREATED,
        )