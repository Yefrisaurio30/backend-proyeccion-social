from rest_framework import serializers
from .models import Publicacion, Categoria


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion']


NUEVOS_CAMPOS = [
    'vistas',
    'programa_nombre', 'programa_codigo',
    'coordinador_nombre', 'coordinador_email', 'sede',
    'fecha_inicio', 'fecha_fin',
    'beneficiarios', 'ubicacion', 'investigador', 'etiquetas',
]


class PublicacionSerializer(serializers.ModelSerializer):
    categoria_detail = CategoriaSerializer(source='categoria', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    imagenes_count = serializers.SerializerMethodField()

    class Meta:
        model = Publicacion
        fields = [
            'id', 'titulo', 'resumen', 'contenido', 'estado',
            'fechaCreacion', 'fechaPublicacion',
            'categoria', 'categoria_detail',
            'usuario', 'usuario_nombre',
            'imagenes_count',
        ] + NUEVOS_CAMPOS
        read_only_fields = ['id', 'fechaCreacion', 'fechaPublicacion', 'usuario', 'vistas']

    def get_imagenes_count(self, obj):
        # Usa la anotación del queryset cuando existe (P1).
        return getattr(obj, 'imagenes_count', obj.imagenes.count())


class PublicacionListSerializer(serializers.ModelSerializer):
    categoria_detail = CategoriaSerializer(source='categoria', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    autor_rol = serializers.SerializerMethodField()
    imagenes_count = serializers.SerializerMethodField()
    comentarios_count = serializers.SerializerMethodField()

    class Meta:
        model = Publicacion
        fields = [
            'id', 'titulo', 'resumen', 'estado',
            'fechaCreacion', 'fechaPublicacion',
            'categoria', 'categoria_detail',
            'usuario_nombre', 'autor_rol',
            'imagenes_count', 'comentarios_count', 'vistas',
            'programa_nombre',
        ]

    def get_imagenes_count(self, obj):
        return getattr(obj, 'imagenes_count', obj.imagenes.count())

    def get_comentarios_count(self, obj):
        if hasattr(obj, 'comentarios_count'):
            return obj.comentarios_count
        return obj.comentarios.count()

    def get_autor_rol(self, obj):
        if obj.usuario.is_superuser or obj.usuario.is_staff:
            return 'Administrador'
        return 'Usuario'


class PublicacionPublicSerializer(serializers.ModelSerializer):
    categoria_detail = CategoriaSerializer(source='categoria', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)
    portada = serializers.SerializerMethodField()
    comentarios_count = serializers.SerializerMethodField()

    class Meta:
        model = Publicacion
        fields = [
            'id', 'titulo', 'resumen', 'contenido', 'estado',
            'fechaCreacion', 'fechaPublicacion',
            'categoria', 'categoria_detail',
            'usuario_nombre', 'portada', 'vistas', 'comentarios_count',
            'etiquetas', 'ubicacion',
        ]

    def get_portada(self, obj):
        # Lee del prefetch (ya ordenado por fechaCarga) sin query extra (P1).
        imagenes = list(obj.imagenes.all())
        return imagenes[0].ruta if imagenes else None

    def get_comentarios_count(self, obj):
        if hasattr(obj, 'comentarios_count'):
            return obj.comentarios_count
        return obj.comentarios.filter(estado='APROBADO').count()