from django.db import models


class Solicitud(models.Model):
    class Tipo(models.TextChoices):
        SOLICITUD = 'SOLICITUD', 'Solicitud'
        PETICION = 'PETICION', 'Peticion'
        QUEJA = 'QUEJA', 'Queja'
        RECLAMO = 'RECLAMO', 'Reclamo'
        SUGERENCIA = 'SUGERENCIA', 'Sugerencia'

    class Estado(models.TextChoices):
        RECIBIDA = 'RECIBIDA', 'Recibida'
        EN_PROCESO = 'EN_PROCESO', 'En proceso'
        RESUELTA = 'RESUELTA', 'Resuelta'
        CERRADA = 'CERRADA', 'Cerrada'

    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.SOLICITUD)
    nombre = models.CharField(max_length=200)
    email = models.EmailField()
    telefono = models.CharField(max_length=30, blank=True, default='')
    asunto = models.CharField(max_length=300)
    mensaje = models.TextField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.RECIBIDA)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name_plural = 'Solicitudes'

    def __str__(self):
        return f'[{self.get_tipo_display()}] {self.asunto} — {self.nombre}'