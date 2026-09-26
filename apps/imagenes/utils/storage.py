"""
Abstraccion de almacenamiento de imagenes.

- IMAGE_STORAGE=local     -> guarda en MEDIA_ROOT (desarrollo / demo local).
- IMAGE_STORAGE=supabase  -> usa Supabase Storage (produccion / servidor futuro).

Para cambiar de uno a otro basta con la variable de entorno, sin tocar codigo.
"""
import os
import uuid

from django.conf import settings


def generate_filename(original_name, publicacion_id):
    ext = os.path.splitext(original_name)[1].lower() or '.jpg'
    base = os.path.splitext(original_name)[0][:40].replace(' ', '_') or 'imagen'
    return f'publicacion_{publicacion_id}/{base}_{uuid.uuid4().hex[:8]}{ext}'


def guardar_imagen(archivo, filename):
    """Guarda el archivo y retorna la URL publica (ruta del modelo)."""
    if getattr(settings, 'IMAGE_STORAGE', 'local') == 'supabase':
        from .supabase import upload_image
        archivo.seek(0)
        return upload_image(archivo, filename)
    return _guardar_local(archivo, filename)


def _guardar_local(archivo, filename):
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile

    archivo.seek(0)
    ruta_relativa = os.path.join('publicaciones', filename).replace('\\', '/')
    ruta_guardada = default_storage.save(ruta_relativa, ContentFile(archivo.read()))
    return settings.MEDIA_URL.rstrip('/') + '/' + ruta_guardada


def eliminar_imagen(ruta):
    """Elimina el archivo fisico de una imagen (solo almacenamiento local)."""
    if getattr(settings, 'IMAGE_STORAGE', 'local') == 'supabase':
        return
    from django.core.files.storage import default_storage

    media_url = settings.MEDIA_URL.rstrip('/') + '/'
    if ruta.startswith(media_url):
        relativa = ruta[len(media_url):]
        if default_storage.exists(relativa):
            default_storage.delete(relativa)
