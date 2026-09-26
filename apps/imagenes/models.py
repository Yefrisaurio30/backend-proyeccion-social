from django.db import models


class Imagen(models.Model):
    nombre = models.CharField(max_length=255)
    ruta = models.URLField(max_length=500, help_text='URL publica en Supabase Storage')
    descripcion = models.TextField(blank=True, default='')
    fechaCarga = models.DateTimeField(auto_now_add=True)
    publicacion = models.ForeignKey(
        'publicaciones.Publicacion',
        on_delete=models.CASCADE,
        related_name='imagenes',
    )

    class Meta:
        verbose_name_plural = 'Imagenes'
        ordering = ['-fechaCarga']

    def __str__(self):
        return f"{self.nombre} - {self.publicacion.titulo}"
