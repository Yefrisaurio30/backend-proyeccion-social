from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import UsuarioRol


ROLES_STAFF = {'Superadmin', 'Coordinación Central', 'Moderador', 'EditorPublicaciones'}


def _sync_is_staff(usuario):
    tiene = usuario.roles_rel.filter(rol__nombre__in=ROLES_STAFF).exists()
    if usuario.is_superuser:
        tiene = True
    if usuario.is_staff != tiene and not usuario.is_superuser:
        # No sobre-escribir superuser
        usuario.is_staff = tiene
        usuario.save(update_fields=['is_staff'])
    elif usuario.is_superuser and not usuario.is_staff:
        usuario.is_staff = True
        usuario.save(update_fields=['is_staff'])


@receiver(post_save, sender=UsuarioRol)
def sync_staff_on_asignar(sender, instance, created, **kwargs):
    if created:
        _sync_is_staff(instance.usuario)


@receiver(post_delete, sender=UsuarioRol)
def sync_staff_on_quitar(sender, instance, **kwargs):
    _sync_is_staff(instance.usuario)
