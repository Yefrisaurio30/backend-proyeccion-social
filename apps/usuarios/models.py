from django.db import models
from django.conf import settings


class Rol(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.CharField(max_length=250, blank=True, default='')
    fechaCreacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Roles'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Permiso(models.Model):
    codename = models.CharField(max_length=80, unique=True)
    nombre = models.CharField(max_length=120)
    modulo = models.CharField(max_length=80, blank=True, default='')

    class Meta:
        verbose_name_plural = 'Permisos'
        ordering = ['codename']

    def __str__(self):
        return self.codename


class RolPermiso(models.Model):
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name='permisos_rel')
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE, related_name='roles_rel')

    class Meta:
        verbose_name_plural = 'Permisos por Rol'
        unique_together = [('rol', 'permiso')]


class UsuarioRol(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='roles_rel')
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name='usuarios_rel')
    asignado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='roles_asignados'
    )
    fechaCreacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Roles por Usuario'
        unique_together = [('usuario', 'rol')]


class Perfil(models.Model):
    class TipoAfiliacion(models.TextChoices):
        ESTUDIANTE = 'ESTUDIANTE', 'Estudiante'
        DOCENTE = 'DOCENTE', 'Docente / Investigador'
        ADMINISTRATIVO = 'ADMINISTRATIVO', 'Administrativo'
        COMUNIDAD = 'COMUNIDAD', 'Comunidad'
        ALIADO = 'ALIADO', 'Aliado externo / ONG'

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil',
    )
    tipo_afiliacion = models.CharField(
        max_length=20,
        choices=TipoAfiliacion.choices,
        default=TipoAfiliacion.COMUNIDAD,
    )
    telefono = models.CharField(max_length=30, blank=True, default='')

    class Meta:
        verbose_name_plural = 'Perfiles'

    def __str__(self):
        return f'Perfil de {self.usuario.username} ({self.get_tipo_afiliacion_display()})'