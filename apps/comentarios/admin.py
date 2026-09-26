from django.contrib import admin
from .models import Comentario


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'usuario', 'publicacion', 'estado',
        'fechaCreacion', 'fechaModeracion',
    ]
    list_filter = ['estado']
    search_fields = ['contenido', 'usuario__username', 'publicacion__titulo']
    readonly_fields = ['fechaCreacion', 'fechaModeracion']
