from django.db import models
from django.conf import settings
from django.utils import timezone


class Comentario(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        APROBADO = 'APROBADO', 'Aprobado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'

    contenido = models.TextField(max_length=500)
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    fechaModeracion = models.DateTimeField(null=True, blank=True)
    motivoRechazo = models.TextField(
        max_length=500,
        blank=True,
        default='',
        help_text='Motivo del rechazo, visible solo para el autor.',
    )
    publicacion = models.ForeignKey(
        'publicaciones.Publicacion',
        on_delete=models.CASCADE,
        related_name='comentarios',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comentarios',
    )

    class Meta:
        verbose_name_plural = 'Comentarios'
        ordering = ['-fechaCreacion']

    def __str__(self):
        return f'{self.usuario.username} en "{self.publicacion.titulo}"'

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old = Comentario.objects.get(pk=self.pk)
                self._estado_anterior = old.estado
            except Comentario.DoesNotExist:
                self._estado_anterior = None
        else:
            self._estado_anterior = None
        super().save(*args, **kwargs)

    def aprobar(self):
        self.estado = self.Estado.APROBADO
        self.fechaModeracion = timezone.now()
        self.save(update_fields=['estado', 'fechaModeracion'])

    def rechazar(self, motivo=''):
        self.estado = self.Estado.RECHAZADO
        self.fechaModeracion = timezone.now()
        self.motivoRechazo = motivo
        self.save(update_fields=['estado', 'fechaModeracion', 'motivoRechazo'])
