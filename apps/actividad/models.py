from django.db import models
from django.conf import settings


class RegistroActividad(models.Model):
    class Accion(models.TextChoices):
        CREAR = 'CREAR', 'Crear'
        EDITAR = 'EDITAR', 'Editar'
        ELIMINAR = 'ELIMINAR', 'Eliminar'
        PUBLICAR = 'PUBLICAR', 'Publicar'
        DESPUBLICAR = 'DESPUBLICAR', 'Despublicar'
        ARCHIVAR = 'ARCHIVAR', 'Archivar'
        APROBAR = 'APROBADO', 'Aprobar'
        RECHAZAR = 'RECHAZADO', 'Rechazar'
        LOGIN = 'LOGIN', 'Iniciar sesion'
        LOGOUT = 'LOGOUT', 'Cerrar sesion'

    accion = models.CharField(max_length=20, choices=Accion.choices)
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(max_length=500)
    modelo = models.CharField(max_length=50, blank=True, default='')
    objeto_id = models.PositiveIntegerField(null=True, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registros_actividad',
    )

    class Meta:
        verbose_name_plural = 'Registros de actividad'
        ordering = ['-fecha']

    def __str__(self):
        return f'[{self.accion}] {self.descripcion[:80]}'
