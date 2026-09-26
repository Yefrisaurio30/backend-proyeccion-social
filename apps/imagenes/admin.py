from django.contrib import admin
from .models import Imagen


@admin.register(Imagen)
class ImagenAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'publicacion', 'fechaCarga']
    list_filter = ['publicacion']
    search_fields = ['nombre']
