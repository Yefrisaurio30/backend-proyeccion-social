from django.db import models
from django.conf import settings


class Reporte(models.Model):
    class Tipo(models.TextChoices):
        GENERAL = 'GENERAL', 'General'
        PUBLICACIONES = 'PUBLICACIONES', 'Publicaciones'
        COMENTARIOS = 'COMENTARIOS', 'Comentarios'
        USUARIOS = 'USUARIOS', 'Usuarios'

    titulo = models.CharField(max_length=200, blank=True, default='')
    tipo = models.CharField(max_length=30, choices=Tipo.choices, default=Tipo.GENERAL)
    parametros = models.JSONField(default=dict, blank=True)
    fechaGeneracion = models.DateTimeField(auto_now_add=True)
    creador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reportes'
    )

    class Meta:
        ordering = ['-fechaGeneracion']
        verbose_name_plural = 'Reportes'

    def __str__(self):
        return f'{self.tipo} {self.fechaGeneracion:%Y-%m-%d}'
