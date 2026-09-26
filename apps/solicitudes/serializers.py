from rest_framework import serializers
from .models import Solicitud


class SolicitudCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solicitud
        fields = ['id', 'tipo', 'nombre', 'email', 'telefono', 'asunto', 'mensaje', 'fecha', 'estado']
        read_only_fields = ['id', 'fecha', 'estado']


class SolicitudAdminSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Solicitud
        fields = [
            'id', 'tipo', 'tipo_display', 'nombre', 'email', 'telefono', 'asunto', 'mensaje',
            'estado', 'estado_display', 'fecha',
        ]
        read_only_fields = ['id', 'fecha', 'tipo', 'nombre', 'email', 'telefono', 'asunto', 'mensaje']


class SolicitudEstadoSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=Solicitud.Estado.choices)