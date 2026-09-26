from django.contrib import admin
from .models import Solicitud


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ['asunto', 'tipo', 'nombre', 'email', 'estado', 'fecha']
    list_filter = ['tipo', 'estado']
    search_fields = ['nombre', 'email', 'asunto', 'mensaje']
    readonly_fields = ['fecha']