from django.contrib import admin
from .models import Publicacion, Categoria


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']


@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'categoria', 'estado', 'vistas', 'fechaCreacion', 'fechaPublicacion']
    list_filter = ['estado', 'categoria']
    search_fields = ['titulo', 'resumen', 'contenido']
    readonly_fields = ['fechaCreacion', 'fechaPublicacion', 'vistas']
