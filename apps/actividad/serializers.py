from rest_framework import serializers
from .models import RegistroActividad


class RegistroActividadSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(
        source='usuario.username', read_only=True, default='Sistema'
    )

    class Meta:
        model = RegistroActividad
        fields = [
            'id', 'accion', 'fecha', 'descripcion',
            'modelo', 'objeto_id',
            'usuario', 'usuario_nombre',
        ]
        read_only_fields = fields
