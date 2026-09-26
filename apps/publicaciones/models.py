from django.db import models
from django.conf import settings


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, default='')

    class Meta:
        verbose_name_plural = 'Categorias'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Publicacion(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = 'BORRADOR', 'Borrador'
        EN_REVISION = 'EN_REVISION', 'En revisión'
        PUBLICADA = 'PUBLICADA', 'Publicada'
        ARCHIVADA = 'ARCHIVADA', 'Archivada'

    titulo = models.CharField(max_length=200)
    resumen = models.TextField(max_length=500, blank=True, default='')
    contenido = models.TextField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.BORRADOR,
    )
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    fechaPublicacion = models.DateTimeField(null=True, blank=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='publicaciones',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='publicaciones',
    )
    # --- Métricas del portal ---
    vistas = models.PositiveIntegerField(default=0)
    # --- Programa institucional asociado (mockup Nueva Publicación, bloque 1) ---
    programa_nombre = models.CharField(max_length=200, blank=True, default='')
    programa_codigo = models.CharField(max_length=50, blank=True, default='')
    coordinador_nombre = models.CharField(max_length=200, blank=True, default='')
    coordinador_email = models.EmailField(blank=True, default='')
    sede = models.CharField(max_length=100, blank=True, default='')
    # --- Información básica (bloque 2) ---
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    # --- Métricas de impacto y alianzas (bloque 5) ---
    beneficiarios = models.PositiveIntegerField(null=True, blank=True)
    ubicacion = models.CharField(max_length=200, blank=True, default='')
    investigador = models.CharField(max_length=200, blank=True, default='')
    etiquetas = models.CharField(max_length=500, blank=True, default='')

    class Meta:
        verbose_name_plural = 'Publicaciones'
        ordering = ['-fechaPublicacion', '-fechaCreacion']

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old = Publicacion.objects.get(pk=self.pk)
                self._estado_anterior = old.estado
            except Publicacion.DoesNotExist:
                self._estado_anterior = None
        else:
            self._estado_anterior = None
        super().save(*args, **kwargs)

    def publicar(self):
        from django.utils import timezone
        self.estado = self.Estado.PUBLICADA
        self.fechaPublicacion = timezone.now()
        self.save(update_fields=['estado', 'fechaPublicacion'])

    def despublicar(self):
        self.estado = self.Estado.BORRADOR
        self.save(update_fields=['estado'])
