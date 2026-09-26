from django.contrib import admin
from .models import RegistroActividad


@admin.register(RegistroActividad)
class RegistroActividadAdmin(admin.ModelAdmin):
    list_display = ['id', 'accion', 'descripcion', 'modelo', 'usuario', 'fecha']
    list_filter = ['accion', 'modelo']
    search_fields = ['descripcion', 'usuario__username']
    readonly_fields = ['fecha']
