from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import RegistroActividad

User = get_user_model()


def _get_usuario(instance):
    usuario = getattr(instance, 'usuario', None)
    if usuario is None:
        usuario = getattr(instance, 'author', None)
    return usuario


@receiver(post_save, sender='publicaciones.Publicacion')
def log_publicacion_save(sender, instance, created, **kwargs):
    usuario = _get_usuario(instance)
    if created:
        RegistroActividad.objects.create(
            accion=RegistroActividad.Accion.CREAR,
            descripcion=f'Se creo la publicacion "{instance.titulo}"',
            modelo='Publicacion',
            objeto_id=instance.pk,
            usuario=usuario,
        )
    else:
        if hasattr(instance, '_estado_anterior') and instance._estado_anterior != instance.estado:
            accion_map = {
                'PUBLICADA': RegistroActividad.Accion.PUBLICAR,
                'BORRADOR': RegistroActividad.Accion.DESPUBLICAR,
                'ARCHIVADA': RegistroActividad.Accion.ARCHIVAR,
                'EN_REVISION': RegistroActividad.Accion.EDITAR,
            }
            accion = accion_map.get(instance.estado, RegistroActividad.Accion.EDITAR)
            desc_map = {
                'PUBLICADA': f'Se publico "{instance.titulo}"',
                'BORRADOR': f'Se despublico "{instance.titulo}"',
                'ARCHIVADA': f'Se archivo "{instance.titulo}"',
                'EN_REVISION': f'Se envio a revisión "{instance.titulo}"',
            }
            descripcion = desc_map.get(instance.estado, f'Se edito "{instance.titulo}"')
            RegistroActividad.objects.create(
                accion=accion,
                descripcion=descripcion,
                modelo='Publicacion',
                objeto_id=instance.pk,
                usuario=usuario,
            )
        else:
            RegistroActividad.objects.create(
                accion=RegistroActividad.Accion.EDITAR,
                descripcion=f'Se edito la publicacion "{instance.titulo}"',
                modelo='Publicacion',
                objeto_id=instance.pk,
                usuario=usuario,
            )


@receiver(post_delete, sender='publicaciones.Publicacion')
def log_publicacion_delete(sender, instance, **kwargs):
    usuario = _get_usuario(instance)
    RegistroActividad.objects.create(
        accion=RegistroActividad.Accion.ELIMINAR,
        descripcion=f'Se elimino la publicacion "{instance.titulo}"',
        modelo='Publicacion',
        objeto_id=instance.pk,
        usuario=usuario,
    )


@receiver(post_save, sender='comentarios.Comentario')
def log_comentario_save(sender, instance, created, **kwargs):
    usuario = _get_usuario(instance)
    if created:
        RegistroActividad.objects.create(
            accion=RegistroActividad.Accion.CREAR,
            descripcion=f'{instance.usuario.username} comento en "{instance.publicacion.titulo}"',
            modelo='Comentario',
            objeto_id=instance.pk,
            usuario=usuario,
        )
    else:
        if hasattr(instance, '_estado_anterior') and instance._estado_anterior != instance.estado:
            if instance.estado == 'APROBADO':
                RegistroActividad.objects.create(
                    accion=RegistroActividad.Accion.APROBAR,
                    descripcion=f'Se aprobo el comentario #{instance.pk} de {instance.usuario.username}',
                    modelo='Comentario',
                    objeto_id=instance.pk,
                    usuario=usuario,
                )
            elif instance.estado == 'RECHAZADO':
                RegistroActividad.objects.create(
                    accion=RegistroActividad.Accion.RECHAZAR,
                    descripcion=f'Se rechazo el comentario #{instance.pk} de {instance.usuario.username}',
                    modelo='Comentario',
                    objeto_id=instance.pk,
                    usuario=usuario,
                )


@receiver(post_delete, sender='comentarios.Comentario')
def log_comentario_delete(sender, instance, **kwargs):
    usuario = _get_usuario(instance)
    RegistroActividad.objects.create(
        accion=RegistroActividad.Accion.ELIMINAR,
        descripcion=f'Se elimino el comentario #{instance.pk}',
        modelo='Comentario',
        objeto_id=instance.pk,
        usuario=usuario,
    )


@receiver(post_save, sender='solicitudes.Solicitud')
def log_solicitud_save(sender, instance, created, **kwargs):
    if created:
        RegistroActividad.objects.create(
            accion=RegistroActividad.Accion.CREAR,
            descripcion=f'Nueva solicitud {instance.get_tipo_display()} de "{instance.nombre}" ({instance.email}): {instance.asunto}',
            modelo='Solicitud',
            objeto_id=instance.pk,
        )
