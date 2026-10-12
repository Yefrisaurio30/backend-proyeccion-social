"""Pruebas Fase 3 (L5, L6).

L5: comentarios públicos con parámetro validado, solo de publicaciones
visibles y paginados.
L6: la moderación no reescribe contenido ni mueve de publicación.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.comentarios.models import Comentario
from apps.publicaciones.models import Categoria, Publicacion


_contador = 0


def _siguiente(prefijo):
    global _contador
    _contador += 1
    return f'{prefijo}_{_contador}'


def crear_pub(usuario, estado=Publicacion.Estado.PUBLICADA, titulo=None):
    categoria, _ = Categoria.objects.get_or_create(
        nombre='CatComentarios', defaults={'descripcion': 'x'})
    return Publicacion.objects.create(
        titulo=titulo or _siguiente('Pub'), resumen='r', contenido='c',
        estado=estado, categoria=categoria, usuario=usuario,
    )


class L5ComentariosPublicosTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user(
            username=_siguiente('autor'), password='Aut12345!')
        self.pub = crear_pub(self.autor)
        self.borrador = crear_pub(
            self.autor, estado=Publicacion.Estado.BORRADOR)
        Comentario.objects.create(
            contenido='Visible', estado=Comentario.Estado.APROBADO,
            publicacion=self.pub, usuario=self.autor)
        Comentario.objects.create(
            contenido='Oculto', estado=Comentario.Estado.APROBADO,
            publicacion=self.borrador, usuario=self.autor)

    def test_parametro_invalido_es_400(self):
        resp = self.client.get(
            '/api/comentarios/publicos/', {'publicacion_id': 'abc'})
        self.assertEqual(resp.status_code, 400)

    def test_solo_publicaciones_visibles(self):
        resp = self.client.get(
            '/api/comentarios/publicos/', {'publicacion_id': self.borrador.pk})
        self.assertEqual(resp.status_code, 200)
        datos = resp.data.get('results', resp.data)
        self.assertEqual(datos, [])

    def test_respuesta_paginada(self):
        resp = self.client.get(
            '/api/comentarios/publicos/', {'publicacion_id': self.pub.pk})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('results', resp.data)
        self.assertEqual(
            [c['contenido'] for c in resp.data['results']], ['Visible'])


class L6ModeracionNoReescribeTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.autor = User.objects.create_user(
            username=_siguiente('autor'), password='Aut12345!')
        self.staff = User.objects.create_user(
            username=_siguiente('staff'), password='Stf12345!',
            is_staff=True, is_superuser=True,
        )
        self.pub = crear_pub(self.autor)
        self.otra = crear_pub(self.autor, titulo='Otra')
        self.comentario = Comentario.objects.create(
            contenido='Original', estado=Comentario.Estado.PENDIENTE,
            publicacion=self.pub, usuario=self.autor)
        self.client.force_authenticate(user=self.staff)

    def test_patch_no_cambia_contenido(self):
        resp = self.client.patch(
            f'/api/comentarios/{self.comentario.pk}/',
            {'contenido': 'Reescrito'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.comentario.refresh_from_db()
        self.assertEqual(self.comentario.contenido, 'Original')

    def test_patch_no_mueve_publicacion(self):
        resp = self.client.patch(
            f'/api/comentarios/{self.comentario.pk}/',
            {'publicacion': self.otra.pk}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.comentario.refresh_from_db()
        self.assertEqual(self.comentario.publicacion_id, self.pub.pk)
