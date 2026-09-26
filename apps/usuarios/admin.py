from django.contrib import admin
from .models import Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo_afiliacion', 'telefono']
    list_filter = ['tipo_afiliacion']
    search_fields = ['usuario__username', 'usuario__email']