"""Pruebas de seguridad Fase 1 (S2, S4).

S2: un usuario no puede borrar ni editar imágenes ajenas.
S4: la subida solo acepta imágenes reales (no .html/.svg/.js).
"""
import tempfile

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.imagenes.models import Imagen
from apps.publicaciones.models import Categoria, Publicacion


def png_valido():
    """Genera un PNG real de 1x1 con Pillow (válido para ImageField)."""
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new('RGB', (1, 1), color='red').save(buf, format='PNG')
    return buf.getvalue()


PNG_MINIMO = None  # se genera por test con png_valido()

_contador = 0


def _siguiente(prefijo):
    global _contador
    _contador += 1
    return f'{prefijo}_{_contador}'


def crear_usuario(username=None):
    return User.objects.create_user(
        username=username or _siguiente('imguser'), password='Img12345!')


def crear_publicacion(usuario, titulo='Pub con imagen'):
    categoria, _ = Categoria.objects.get_or_create(
        nombre='CatImagenes', defaults={'descripcion': 'x'})
    return Publicacion.objects.create(
        titulo=titulo, resumen='r', contenido='c',
        estado=Publicacion.Estado.PUBLICADA,
        categoria=categoria, usuario=usuario,
    )


class S2ImagenesAjenasTest(TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._override = override_settings(MEDIA_ROOT=self._tmp.name)
        self._override.enable()
        self.addCleanup(self._override.disable)
        self.addCleanup(self._tmp.cleanup)
        self.client = APIClient()
        self.autor = crear_usuario()
        self.intruso = crear_usuario()
        self.pub = crear_publicacion(self.autor)
        self.imagen = Imagen.objects.create(
            nombre='Portada', ruta='/media/publicaciones/x.png',
            descripcion='', publicacion=self.pub,
        )

    def test_usuario_no_borra_imagen_ajena(self):
        self.client.force_authenticate(user=self.intruso)
        resp = self.client.delete(f'/api/imagenes/imagenes/{self.imagen.pk}/')
        self.assertIn(resp.status_code, [401, 403, 404])
        self.assertTrue(Imagen.objects.filter(pk=self.imagen.pk).exists())

    def test_usuario_no_edita_imagen_ajena(self):
        self.client.force_authenticate(user=self.intruso)
        resp = self.client.patch(f'/api/imagenes/imagenes/{self.imagen.pk}/', {
            'nombre': 'Hackeada',
        }, format='json')
        self.assertIn(resp.status_code, [401, 403, 404])
        self.imagen.refresh_from_db()
        self.assertEqual(self.imagen.nombre, 'Portada')

    def test_usuario_no_mueve_imagen_a_su_publicacion(self):
        self.client.force_authenticate(user=self.intruso)
        mia = crear_publicacion(self.intruso, titulo='Mía')
        resp = self.client.patch(f'/api/imagenes/imagenes/{self.imagen.pk}/', {
            'publicacion': mia.pk,
        }, format='json')
        self.assertIn(resp.status_code, [400, 401, 403, 404])
        self.imagen.refresh_from_db()
        self.assertEqual(self.imagen.publicacion_id, self.pub.pk)


class S4TipoArchivoTest(TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._override = override_settings(MEDIA_ROOT=self._tmp.name)
        self._override.enable()
        self.addCleanup(self._override.disable)
        self.addCleanup(self._tmp.cleanup)
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username=_siguiente('staff'), password='Stf12345!',
            is_staff=True, is_superuser=True,
        )
        self.pub = crear_publicacion(self.staff)
        self.client.force_authenticate(user=self.staff)
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.SimpleUploadedFile = SimpleUploadedFile

    def _subir(self, nombre, contenido, content_type):
        archivo = self.SimpleUploadedFile(nombre, contenido, content_type=content_type)
        return self.client.post('/api/imagenes/imagenes/', {
            'archivo': archivo, 'publicacion': self.pub.pk, 'nombre': nombre,
        }, format='multipart')

    def test_rechaza_html(self):
        resp = self._subir(
            'xss.html', b'<script>alert(1)</script>', 'text/html')
        self.assertEqual(resp.status_code, 400)

    def test_rechaza_svg(self):
        resp = self._subir(
            'vector.svg', b'<svg xmlns="http://www.w3.org/2000/svg"></svg>',
            'image/svg+xml')
        self.assertEqual(resp.status_code, 400)

    def test_rechaza_js(self):
        resp = self._subir('codigo.js', b'alert(1)', 'text/javascript')
        self.assertEqual(resp.status_code, 400)

    def test_acepta_png_real(self):
        resp = self._subir('portada.png', png_valido(), 'image/png')
        self.assertEqual(resp.status_code, 201)


class T2ErroresAlmacenamientoTest(TestCase):
    """Fallo de Supabase devuelve mensaje claro, no 500 (T2)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._override = override_settings(MEDIA_ROOT=self._tmp.name)
        self._override.enable()
        self.addCleanup(self._override.disable)
        self.addCleanup(self._tmp.cleanup)
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username=_siguiente('staff'), password='Stf12345!',
            is_staff=True, is_superuser=True,
        )
        self.pub = crear_publicacion(self.staff)
        self.client.force_authenticate(user=self.staff)

    def test_fallo_supabase_es_502_con_mensaje(self):
        from unittest import mock
        from django.core.files.uploadedfile import SimpleUploadedFile
        with override_settings(IMAGE_STORAGE='supabase'):
            with mock.patch(
                'apps.imagenes.utils.supabase.upload_image',
                side_effect=Exception('bucket caído'),
            ):
                archivo = SimpleUploadedFile(
                    'falla.png', png_valido(), content_type='image/png')
                resp = self.client.post('/api/imagenes/imagenes/', {
                    'archivo': archivo, 'publicacion': self.pub.pk,
                    'nombre': 'Falla',
                }, format='multipart')
        self.assertEqual(resp.status_code, 502)
        self.assertIn('almacenamiento', resp.data['detail'].lower())


class L7AlmacenamientoTest(TestCase):
    """Borrado en Supabase, ruta local válida y limpieza en cascada (L7)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._override = override_settings(MEDIA_ROOT=self._tmp.name)
        self._override.enable()
        self.addCleanup(self._override.disable)
        self.addCleanup(self._tmp.cleanup)
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username=_siguiente('staff'), password='Stf12345!',
            is_staff=True, is_superuser=True,
        )
        self.pub = crear_publicacion(self.staff)
        self.client.force_authenticate(user=self.staff)

    def test_ruta_local_pasa_validacion(self):
        imagen = Imagen(
            nombre='X', ruta='/media/publicaciones/x.png',
            descripcion='', publicacion=self.pub,
        )
        imagen.full_clean()  # URLField la rechaza; CharField la acepta.

    def test_supabase_borra_del_bucket(self):
        from unittest import mock
        with override_settings(IMAGE_STORAGE='supabase', SUPABASE_BUCKET='bkt'):
            with mock.patch(
                'apps.imagenes.utils.supabase.delete_image'
            ) as mock_delete:
                from apps.imagenes.utils.storage import eliminar_imagen
                eliminar_imagen(
                    'https://xyz.supabase.co/storage/v1/object/public/bkt/pub/a.png')
        mock_delete.assert_called_once_with('pub/a.png')

    def test_borrar_publicacion_limpia_archivos(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.core.files.storage import default_storage
        archivo = SimpleUploadedFile(
            'cascada.png', png_valido(), content_type='image/png')
        resp = self.client.post('/api/imagenes/imagenes/', {
            'archivo': archivo, 'publicacion': self.pub.pk, 'nombre': 'C',
        }, format='multipart')
        self.assertEqual(resp.status_code, 201)
        ruta = Imagen.objects.get(pk=resp.data['id']).ruta
        relativa = ruta.replace('/media/', '', 1)
        self.assertTrue(default_storage.exists(relativa))
        self.pub.delete()
        self.assertFalse(default_storage.exists(relativa))
