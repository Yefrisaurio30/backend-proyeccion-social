from rest_framework import serializers
from .models import Imagen

MAX_TAMANO_BYTES = 10 * 1024 * 1024  # 10 MB (igual que el mockup del portal)


class ImagenSerializer(serializers.ModelSerializer):
    publicacion_titulo = serializers.CharField(
        source='publicacion.titulo', read_only=True
    )

    class Meta:
        model = Imagen
        fields = [
            'id', 'nombre', 'ruta', 'descripcion',
            'fechaCarga', 'publicacion', 'publicacion_titulo',
        ]
        read_only_fields = ['id', 'fechaCarga', 'ruta']


class ImagenUploadSerializer(serializers.ModelSerializer):
    archivo = serializers.FileField(write_only=True)

    class Meta:
        model = Imagen
        fields = ['id', 'archivo', 'nombre', 'descripcion', 'publicacion']

    def validate_archivo(self, archivo):
        if archivo.size > MAX_TAMANO_BYTES:
            raise serializers.ValidationError(
                'El archivo supera el maximo permitido de 10 MB.'
            )
        return archivo

    def create(self, validated_data):
        from .utils.storage import guardar_imagen, generate_filename

        archivo = validated_data.pop('archivo')
        publicacion = validated_data['publicacion']
        nombre = validated_data.get('nombre', archivo.name)

        filename = generate_filename(archivo.name, publicacion.id)
        ruta = guardar_imagen(archivo, filename)

        imagen = Imagen.objects.create(
            nombre=nombre,
            ruta=ruta,
            descripcion=validated_data.get('descripcion', ''),
            publicacion=publicacion,
        )
        return imagen