"""Al borrar una Imagen (directo o en cascada) se borra también su archivo (L7)."""
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Imagen


@receiver(post_delete, sender=Imagen)
def eliminar_archivo_al_borrar(sender, instance, **kwargs):
    from .utils.storage import eliminar_imagen
    if instance.ruta:
        eliminar_imagen(instance.ruta)
