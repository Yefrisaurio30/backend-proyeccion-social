from rest_framework import serializers
from .models import Comentario


class ComentarioCreateSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Comentario
        fields = [
            'id', 'contenido', 'publicacion',
            'usuario', 'usuario_nombre', 'estado',
        ]
        read_only_fields = ['id', 'usuario', 'estado']

    def validate_publicacion(self, publicacion):
        from apps.publicaciones.models import Publicacion
        if publicacion.estado != Publicacion.Estado.PUBLICADA:
            raise serializers.ValidationError(
                'Solo se pueden comentar publicaciones publicadas.'
            )
        return publicacion

    def validate_contenido(self, value):
        if len(value) > 500:
            raise serializers.ValidationError('El comentario no puede exceder 500 caracteres.')
        return value


class ComentarioPublicSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = Comentario
        fields = [
            'id', 'contenido', 'fechaCreacion',
            'usuario_nombre',
        ]


class ComentarioModerationSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    publicacion_titulo = serializers.CharField(
        source='publicacion.titulo', read_only=True
    )

    class Meta:
        model = Comentario
        fields = [
            'id', 'contenido', 'fechaCreacion', 'estado',
            'fechaModeracion', 'motivoRechazo',
            'publicacion', 'publicacion_titulo',
            'usuario', 'usuario_nombre',
        ]
        # La moderación no reescribe lo que escribió el usuario (L6):
        # contenido y publicacion son de solo lectura.
        read_only_fields = [
            'id', 'contenido', 'fechaCreacion', 'estado', 'fechaModeracion',
            'motivoRechazo', 'publicacion', 'usuario',
        ]


class ComentarioRechazarSerializer(serializers.Serializer):
    motivo = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        default='',
    )
