"""Pruebas Fase 2 (L3): la trazabilidad registra a quien actúa, no al autor."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.actividad.models import RegistroActividad
from apps.comentarios.models import Comentario
from apps.publicaciones.models import Categoria, Publicacion

_contador = 0


def _siguiente(prefijo):
    global _contador
    _contador += 1
    return f'{prefijo}_{_contador}'


class L3AuditoriaActorTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user(
            username=_siguiente('autor'), password='Aut12345!')
        self.moderador = User.objects.create_user(
            username=_siguiente('mod'), password='Mod12345!',
            is_staff=True, is_superuser=True,
        )
        categoria = Categoria.objects.create(nombre=_siguiente('Cat'))
        self.pub = Publicacion.objects.create(
            titulo='Pub L3', resumen='r', contenido='c',
            estado=Publicacion.Estado.BORRADOR,
            categoria=categoria, usuario=self.autor,
        )
        self.comentario = Comentario.objects.create(
            contenido='Comentario L3', publicacion=self.pub, usuario=self.autor)

    def test_aprobar_registra_al_moderador(self):
        self.assertTrue(self.client.login(
            username=self.moderador.username, password='Mod12345!'))
        resp = self.client.patch(f'/api/comentarios/{self.comentario.pk}/aprobar/')
        self.assertEqual(resp.status_code, 200)
        reg = RegistroActividad.objects.filter(
            modelo='Comentario', objeto_id=self.comentario.pk,
            accion=RegistroActividad.Accion.APROBAR,
        ).latest('id')
        self.assertEqual(reg.usuario_id, self.moderador.pk)

    def test_publicar_registra_al_admin(self):
        self.assertTrue(self.client.login(
            username=self.moderador.username, password='Mod12345!'))
        resp = self.client.post(
            f'/api/publicaciones/publicaciones/{self.pub.pk}/publicar/')
        self.assertEqual(resp.status_code, 200)
        reg = RegistroActividad.objects.filter(
            modelo='Publicacion', objeto_id=self.pub.pk,
            accion=RegistroActividad.Accion.PUBLICAR,
        ).latest('id')
        self.assertEqual(reg.usuario_id, self.moderador.pk)
