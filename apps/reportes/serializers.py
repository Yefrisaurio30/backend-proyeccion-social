from rest_framework import serializers
from .models import Reporte


class ReporteSerializer(serializers.ModelSerializer):
    creador_nombre = serializers.CharField(source='creador.username', read_only=True)

    class Meta:
        model = Reporte
        fields = ['id', 'titulo', 'tipo', 'parametros', 'fechaGeneracion', 'creador', 'creador_nombre']
        read_only_fields = ['id', 'fechaGeneracion', 'creador']
