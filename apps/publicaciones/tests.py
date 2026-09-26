from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.publicaciones.models import Publicacion, Categoria
from apps.comentarios.models import Comentario
from apps.actividad.models import RegistroActividad

_user_counter = 0
_categoria_counter = 0


def crear_usuario(username=None, password='Test1234!', **kwargs):
    global _user_counter
    _user_counter += 1
    if username is None:
        username = f'testuser_{_user_counter}'
    return User.objects.create_user(username=username, password=password, **kwargs)


def crear_staff(username=None, password='Staff1234!'):
    global _user_counter
    _user_counter += 1
    if username is None:
        username = f'staffuser_{_user_counter}'
    return User.objects.create_user(
        username=username, password=password,
        is_staff=True, is_superuser=True,
    )


def crear_categoria(nombre=None):
    global _categoria_counter
    _categoria_counter += 1
    if nombre is None:
        nombre = f'Tecnologia_{_categoria_counter}'
    return Categoria.objects.create(nombre=nombre, descripcion=f'Descripcion de {nombre}')


def crear_publicacion(estado=Publicacion.Estado.PUBLICADA, usuario=None, categoria=None, **overrides):
    if usuario is None:
        usuario = crear_usuario()
    if categoria is None:
        categoria = crear_categoria()
    defaults = {
        'titulo': 'Publicacion de prueba',
        'resumen': 'Resumen de prueba',
        'contenido': 'Contenido completo de la publicacion de prueba.',
        'estado': estado,
        'categoria': categoria,
        'usuario': usuario,
    }
    defaults.update(overrides)
    pub = Publicacion.objects.create(**defaults)
    if estado == Publicacion.Estado.PUBLICADA:
        pub.fechaPublicacion = pub.fechaCreacion
        pub.save(update_fields=['fechaPublicacion'])
    return pub


def crear_comentario(publicacion, usuario, estado=Comentario.Estado.PENDIENTE, **overrides):
    defaults = {
        'contenido': 'Comentario de prueba',
        'estado': estado,
        'publicacion': publicacion,
        'usuario': usuario,
    }
    defaults.update(overrides)
    return Comentario.objects.create(**defaults)


# ======================================================================
# CU-01: Consultar publicaciones (Anonimo)
# CU-03: Ver detalle de publicacion (Anonimo)
# ======================================================================


class CU01_ConsultarPublicacionesAnonimoTest(TestCase):
    """CU-01: Un visitante puede listar publicaciones publicadas sin autenticarse."""

    def setUp(self):
        self.client = APIClient()
        self.pub_publicada = crear_publicacion(estado=Publicacion.Estado.PUBLICADA)
        self.pub_borrador = crear_publicacion(estado=Publicacion.Estado.BORRADOR, titulo='Borrador oculto')

    def test_lista_solo_publicadas(self):
        resp = self.client.get('/api/publicaciones/publicas/')
        self.assertEqual(resp.status_code, 200)
        titulos = [p['titulo'] for p in resp.data.get('results', resp.data)]
        self.assertIn(self.pub_publicada.titulo, titulos)
        self.assertNotIn(self.pub_borrador.titulo, titulos)

    def test_archivada_visible_como_completado(self):
        archivada = crear_publicacion(estado=Publicacion.Estado.ARCHIVADA, titulo='Proyecto culminado')
        resp = self.client.get('/api/publicaciones/publicas/')
        self.assertEqual(resp.status_code, 200)
        por_id = {p['id']: p for p in resp.data.get('results', resp.data)}
        self.assertIn(archivada.pk, por_id)
        self.assertEqual(por_id[archivada.pk]['estado'], 'ARCHIVADA')

    def test_detalle_publicacion(self):
        resp = self.client.get(f'/api/publicaciones/publicas/{self.pub_publicada.pk}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['titulo'], self.pub_publicada.titulo)

    def test_detalle_borrador_no_accesible(self):
        resp = self.client.get(f'/api/publicaciones/publicas/{self.pub_borrador.pk}/')
        self.assertEqual(resp.status_code, 404)


# ======================================================================
# CU-02: Buscar publicaciones (Anonimo)
# ======================================================================


class CU02_BuscarPublicacionesTest(TestCase):
    """CU-02: Busqueda por texto y filtros en publicaciones publicas."""

    def setUp(self):
        self.client = APIClient()
        self.pub1 = crear_publicacion(titulo='Inteligencia Artificial', estado=Publicacion.Estado.PUBLICADA)
        self.pub2 = crear_publicacion(titulo='Desarrollo Web', estado=Publicacion.Estado.PUBLICADA)

    def test_busqueda_por_texto(self):
        resp = self.client.get('/api/publicaciones/publicas/', {'search': 'Inteligencia'})
        self.assertEqual(resp.status_code, 200)
        titulos = [p['titulo'] for p in resp.data.get('results', resp.data)]
        self.assertIn('Inteligencia Artificial', titulos)
        self.assertNotIn('Desarrollo Web', titulos)

    def test_filtro_por_categoria(self):
        resp = self.client.get('/api/publicaciones/publicas/', {'categoria': self.pub1.categoria.pk})
        self.assertEqual(resp.status_code, 200)


# ======================================================================
# CU-03: Ver detalle de publicacion (Anonimo)
# ======================================================================


class CU03_DetallePublicacionTest(TestCase):
    """CU-03: Ver detalle completo con contenido, autor, fecha, imagenes."""

    def setUp(self):
        self.client = APIClient()
        self.usuario = crear_usuario()
        self.pub = crear_publicacion(usuario=self.usuario)

    def test_detalle_contiene_campos_requeridos(self):
        resp = self.client.get(f'/api/publicaciones/publicas/{self.pub.pk}/')
        self.assertEqual(resp.status_code, 200)
        for campo in ['titulo', 'resumen', 'contenido', 'categoria', 'fechaCreacion', 'fechaPublicacion']:
            self.assertIn(campo, resp.data)


# ======================================================================
# CU-04: Ver comentarios aprobados (Anonimo)
# ======================================================================


class CU04_ComentariosAprobadosTest(TestCase):
    """CU-04: Solo comentarios con estado APROBADO son visibles publicamente."""

    def setUp(self):
        self.client = APIClient()
        self.pub = crear_publicacion()
        self.usuario = crear_usuario()
        self.comentario_aprobado = crear_comentario(
            self.pub, self.usuario, estado=Comentario.Estado.APROBADO, contenido='Aprobado'
        )
        self.comentario_pendiente = crear_comentario(
            self.pub, self.usuario, estado=Comentario.Estado.PENDIENTE, contenido='Pendiente'
        )

    def test_solo_aprobados_visibles(self):
        resp = self.client.get('/api/comentarios/publicos/', {'publicacion_id': self.pub.pk})
        self.assertEqual(resp.status_code, 200)
        contenidos = [c['contenido'] for c in resp.data]
        self.assertIn('Aprobado', contenidos)
        self.assertNotIn('Pendiente', contenidos)


# ======================================================================
# CU-05: Registrar usuario
# ======================================================================


class CU05_RegistrarUsuarioTest(TestCase):
    """CU-05: Registro publico de usuario (endpoint /api/auth/register/)."""

    def test_creacion_usuario_via_admin(self):
        user = User.objects.create_user('nuevousuario', 'correo@test.com', 'Password123!')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_registro_endpoint_crea_perfil(self):
        client = APIClient()
        resp = client.post('/api/auth/register/', {
            'username': 'registrotest',
            'email': 'registro@test.com',
            'password': 'Password123!',
            'password2': 'Password123!',
            'nombre_completo': 'Ana Maria Lopez',
            'tipo_afiliacion': 'ESTUDIANTE',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        user = User.objects.get(username='registrotest')
        self.assertEqual(user.first_name, 'Ana')
        self.assertEqual(user.perfil.tipo_afiliacion, 'ESTUDIANTE')

    def test_usuario_no_staff_no_acceso_moderacion(self):
        user = crear_usuario()
        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.get('/api/comentarios/')
        self.assertIn(resp.status_code, [403, 401])


# ======================================================================
# CU-06: Iniciar sesion
# ======================================================================


class CU06_IniciarSesionTest(TestCase):
    """CU-06: Login con credenciales validas via session auth."""

    def setUp(self):
        self.client = APIClient()
        self.user = crear_usuario()

    def test_usuario_autenticado_puede_crear_comentario(self):
        self.client.force_authenticate(user=self.user)
        pub = crear_publicacion()
        resp = self.client.post('/api/comentarios/', {
            'publicacion': pub.pk,
            'contenido': 'Mi comentario',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['estado'], 'PENDIENTE')


# ======================================================================
# CU-07: Crear comentario
# ======================================================================


class CU07_CrearComentarioTest(TestCase):
    """CU-07: Usuario autenticado crea comentario con estado PENDIENTE."""

    def setUp(self):
        self.client = APIClient()
        self.user = crear_usuario()
        self.pub = crear_publicacion()
        self.client.force_authenticate(user=self.user)

    def test_crear_comentario_pendiente(self):
        resp = self.client.post('/api/comentarios/', {
            'publicacion': self.pub.pk,
            'contenido': 'Excelente publicacion',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['estado'], 'PENDIENTE')

    def test_anonimo_no_puede_crear_comentario(self):
        client = APIClient()
        resp = client.post('/api/comentarios/', {
            'publicacion': self.pub.pk,
            'contenido': 'Spam',
        }, format='json')
        self.assertIn(resp.status_code, [401, 403])


# ======================================================================
# CU-08: Moderar comentario (aprobar/rechazar)
# ======================================================================


class CU08_ModerarComentarioTest(TestCase):
    """CU-08: Staff aprueba o rechaza comentarios pendientes."""

    def setUp(self):
        self.client = APIClient()
        self.staff = crear_staff()
        self.user = crear_usuario()
        self.pub = crear_publicacion()
        self.comentario = crear_comentario(self.pub, self.user)
        self.client.force_authenticate(user=self.staff)

    def test_aprobar_comentario(self):
        resp = self.client.patch(f'/api/comentarios/{self.comentario.pk}/aprobar/')
        self.assertEqual(resp.status_code, 200)
        self.comentario.refresh_from_db()
        self.assertEqual(self.comentario.estado, Comentario.Estado.APROBADO)
        self.assertIsNotNone(self.comentario.fechaModeracion)

    def test_rechazar_comentario(self):
        resp = self.client.patch(
            f'/api/comentarios/{self.comentario.pk}/rechazar/',
            {'motivo': 'Contenido inapropiado'}, format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.comentario.refresh_from_db()
        self.assertEqual(self.comentario.estado, Comentario.Estado.RECHAZADO)
        self.assertEqual(self.comentario.motivoRechazo, 'Contenido inapropiado')

    def test_no_aprobar_comentario_ya_aprobado(self):
        self.comentario.aprobar()
        resp = self.client.patch(f'/api/comentarios/{self.comentario.pk}/aprobar/')
        self.assertEqual(resp.status_code, 400)

    def test_visitante_no_puede_moderar(self):
        client = APIClient()
        user = crear_usuario()
        client.force_authenticate(user=user)
        resp = client.patch(f'/api/comentarios/{self.comentario.pk}/aprobar/')
        self.assertIn(resp.status_code, [403, 401])

    def test_cola_pendientes(self):
        resp = self.client.get('/api/comentarios/pendientes/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)


# ======================================================================
# CU-09: Crear borrador
# ======================================================================


class CU09_CrearBorradorTest(TestCase):
    """CU-09: Staff crea una publicacion en estado BORRADOR."""

    def setUp(self):
        self.client = APIClient()
        self.staff = crear_staff()
        self.categoria = crear_categoria()
        self.client.force_authenticate(user=self.staff)

    def test_crear_borrador(self):
        resp = self.client.post('/api/publicaciones/publicaciones/', {
            'titulo': 'Nuevo borrador',
            'resumen': 'Resumen',
            'contenido': 'Contenido del borrador.',
            'categoria': self.categoria.pk,
            'estado': 'BORRADOR',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['estado'], 'BORRADOR')
        pub = Publicacion.objects.get(pk=resp.data['id'])
        self.assertEqual(pub.usuario, self.staff)


# ======================================================================
# CU-10: Publicar borrador
# ======================================================================


class CU10_PublicarBorradorTest(TestCase):
    """CU-10: Cambiar estado de BORRADOR a PUBLICADA con fecha de publicacion."""

    def setUp(self):
        self.client = APIClient()
        self.staff = crear_staff()
        self.pub = crear_publicacion(estado=Publicacion.Estado.BORRADOR, usuario=self.staff)
        self.client.force_authenticate(user=self.staff)

    def test_publicar_borrador(self):
        resp = self.client.post(f'/api/publicaciones/publicaciones/{self.pub.pk}/publicar/')
        self.assertEqual(resp.status_code, 200)
        self.pub.refresh_from_db()
        self.assertEqual(self.pub.estado, Publicacion.Estado.PUBLICADA)
        self.assertIsNotNone(self.pub.fechaPublicacion)

    def test_publicar_ya_publicada_falla(self):
        self.pub.publicar()
        resp = self.client.post(f'/api/publicaciones/publicaciones/{self.pub.pk}/publicar/')
        self.assertEqual(resp.status_code, 400)


# ======================================================================
# CU-11: Despublicar publicacion
# ======================================================================


class CU11_DespublicarTest(TestCase):
    """CU-11: Publicacion PUBLICADA vuelve a BORRADOR."""

    def setUp(self):
        self.client = APIClient()
        self.staff = crear_staff()
        self.pub = crear_publicacion(estado=Publicacion.Estado.PUBLICADA, usuario=self.staff)
        self.client.force_authenticate(user=self.staff)

    def test_despublicar(self):
        resp = self.client.post(f'/api/publicaciones/publicaciones/{self.pub.pk}/despublicar/')
        self.assertEqual(resp.status_code, 200)
        self.pub.refresh_from_db()
        self.assertEqual(self.pub.estado, Publicacion.Estado.BORRADOR)


# ======================================================================
# CU-12: Archivar publicacion
# ======================================================================


class CU12_ArchivarPublicacionTest(TestCase):
    """CU-12: Archivar publicacion (cualquier estado)."""

    def setUp(self):
        self.client = APIClient()
        self.staff = crear_staff()
        self.pub = crear_publicacion(estado=Publicacion.Estado.PUBLICADA, usuario=self.staff)
        self.client.force_authenticate(user=self.staff)

    def test_archivar(self):
        resp = self.client.post(f'/api/publicaciones/publicaciones/{self.pub.pk}/archivar/')
        self.assertEqual(resp.status_code, 200)
        self.pub.refresh_from_db()
        self.assertEqual(self.pub.estado, Publicacion.Estado.ARCHIVADA)


# ======================================================================
# CU-13: CRUD Categorias
# ======================================================================


class CU13_CRUDCategoriasTest(TestCase):
    """CU-13: Gestor puede crear, listar, editar y eliminar categorias."""

    def setUp(self):
        self.client = APIClient()
        self.staff = crear_staff()
        self.client.force_authenticate(user=self.staff)

    def test_listar_categorias(self):
        crear_categoria('Matematicas')
        resp = self.client.get('/api/publicaciones/categorias/')
        self.assertEqual(resp.status_code, 200)

    def test_crear_categoria(self):
        resp = self.client.post('/api/publicaciones/categorias/', {
            'nombre': 'Ciencias',
            'descripcion': 'Area de ciencias',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Categoria.objects.filter(nombre='Ciencias').exists())

    def test_eliminar_categoria(self):
        cat = crear_categoria('Temporal')
        resp = self.client.delete(f'/api/publicaciones/categorias/{cat.pk}/')
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(Categoria.objects.filter(pk=cat.pk).exists())


# ======================================================================
# CU-14: CRUD Imagenes
# ======================================================================


class CU14_CRUDImagenesTest(TestCase):
    """CU-14: Gestor puede gestionar imagenes (listar). Upload requiere Supabase."""

    def setUp(self):
        self.client = APIClient()
        self.staff = crear_staff()
        self.pub = crear_publicacion(usuario=self.staff)
        self.client.force_authenticate(user=self.staff)

    def test_listar_imagenes(self):
        resp = self.client.get('/api/imagenes/imagenes/')
        self.assertEqual(resp.status_code, 200)


# ======================================================================
# CU-15: Trazabilidad / Registro de actividad
# ======================================================================


class CU15_TrazabilidadTest(TestCase):
    """CU-15: El sistema registra automaticamente la actividad (signals)."""

    def test_registro_creacion_publicacion(self):
        staff = crear_staff()
        pub = crear_publicacion(estado=Publicacion.Estado.BORRADOR, usuario=staff)
        registros = RegistroActividad.objects.filter(modelo='Publicacion', objeto_id=pub.pk)
        self.assertTrue(registros.filter(accion=RegistroActividad.Accion.CREAR).exists())

    def test_registro_estado_publicar(self):
        staff = crear_staff()
        pub = crear_publicacion(estado=Publicacion.Estado.BORRADOR, usuario=staff)
        pub.publicar()
        registros = RegistroActividad.objects.filter(modelo='Publicacion', objeto_id=pub.pk)
        self.assertTrue(registros.filter(accion=RegistroActividad.Accion.PUBLICAR).exists())

    def test_registro_creacion_comentario(self):
        user = crear_usuario()
        pub = crear_publicacion()
        comentario = crear_comentario(pub, user)
        registros = RegistroActividad.objects.filter(modelo='Comentario', objeto_id=comentario.pk)
        self.assertTrue(registros.filter(accion=RegistroActividad.Accion.CREAR).exists())

    def test_trazabilidad_solo_staff(self):
        client = APIClient()
        staff = crear_staff()
        client.force_authenticate(user=staff)
        resp = client.get('/api/registros/')
        self.assertEqual(resp.status_code, 200)


# ======================================================================
# CU-16: Dashboard / Metricas
# ======================================================================


class CU16_DashboardTest(TestCase):
    """CU-16: Dashboard retorna metricas consolidadas."""

    def setUp(self):
        self.client = APIClient()
        self.staff = crear_staff()
        self.client.force_authenticate(user=self.staff)

    def test_dashboard_metricas(self):
        crear_publicacion(estado=Publicacion.Estado.PUBLICADA, usuario=self.staff)
        crear_publicacion(estado=Publicacion.Estado.BORRADOR, usuario=self.staff)
        crear_publicacion(estado=Publicacion.Estado.EN_REVISION, usuario=self.staff, titulo='En revision')
        resp = self.client.get('/api/reportes/dashboard/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('publicaciones', resp.data)
        self.assertIn('comentarios', resp.data)
        self.assertIn('usuarios', resp.data)
        self.assertEqual(resp.data['publicaciones']['total'], 3)
        self.assertEqual(resp.data['publicaciones']['en_revision'], 1)
        self.assertIn('nuevas', resp.data['publicaciones'])
        self.assertIn('publicaciones_recientes', resp.data)

    def test_dashboard_no_acceso_anonimo(self):
        client = APIClient()
        resp = client.get('/api/reportes/dashboard/')
        self.assertIn(resp.status_code, [401, 403])


# ======================================================================
# CU-17: Reportes y exportacion CSV
# ======================================================================


class CU17_ReportesTest(TestCase):
    """CU-17: Reportes con filtros por fecha y categoria."""

    def setUp(self):
        self.client = APIClient()
        self.staff = crear_staff()
        self.pub = crear_publicacion(estado=Publicacion.Estado.PUBLICADA, usuario=self.staff)
        self.client.force_authenticate(user=self.staff)

    def test_reporte_con_filtro_estado(self):
        resp = self.client.get('/api/publicaciones/publicaciones/', {'estado': 'PUBLICADA'})
        self.assertEqual(resp.status_code, 200)

    def test_reporte_con_filtro_categoria(self):
        resp = self.client.get('/api/publicaciones/publicaciones/', {'categoria': self.pub.categoria.pk})
        self.assertEqual(resp.status_code, 200)


# ======================================================================
# CU-18: Control de permisos (RBAC)
# ======================================================================


class CU18_PermisosTest(TestCase):
    """CU-18: Visitante/Usuario NO puede acceder a endpoints protegidos."""

    def setUp(self):
        self.client = APIClient()
        self.usuario = crear_usuario()
        self.staff = crear_staff()
        self.pub = crear_publicacion()
        self.comentario = crear_comentario(self.pub, self.usuario)

    def test_visitante_no_acceso_actividad(self):
        resp = self.client.get('/api/registros/')
        self.assertIn(resp.status_code, [401, 403])

    def test_visitante_no_acceso_dashboard(self):
        resp = self.client.get('/api/reportes/dashboard/')
        self.assertIn(resp.status_code, [401, 403])

    def test_usuario_no_staff_no_acceso_pendientes(self):
        self.client.force_authenticate(user=self.usuario)
        resp = self.client.get('/api/comentarios/pendientes/')
        self.assertIn(resp.status_code, [403, 401])

    def test_usuario_no_staff_no_aprobar(self):
        self.client.force_authenticate(user=self.usuario)
        resp = self.client.patch(f'/api/comentarios/{self.comentario.pk}/aprobar/')
        self.assertIn(resp.status_code, [403, 401])

    def test_staff_acceso_completo(self):
        self.client.force_authenticate(user=self.staff)
        self.assertEqual(self.client.get('/api/registros/').status_code, 200)
        self.assertEqual(self.client.get('/api/reportes/dashboard/').status_code, 200)
        self.assertEqual(self.client.get('/api/comentarios/pendientes/').status_code, 200)

    def test_anonimo_acceso_publico(self):
        self.assertEqual(self.client.get('/api/publicaciones/publicas/').status_code, 200)
        resp = self.client.get('/api/comentarios/publicos/', {'publicacion_id': self.pub.pk})
        self.assertEqual(resp.status_code, 200)


# ======================================================================
# Flujo E2E Integrado: Publicacion completa
# ======================================================================


class FlujoCompletoPublicacionTest(TestCase):
    """E2E: Crear borrador -> Publicar -> Aparecer en API publica -> Archivar."""

    def setUp(self):
        self.client = APIClient()
        self.staff = crear_staff()
        self.categoria = crear_categoria()
        self.client.force_authenticate(user=self.staff)

    def test_flujo_completo_publicacion(self):
        # 1. Crear borrador
        resp = self.client.post('/api/publicaciones/publicaciones/', {
            'titulo': 'Articulo E2E',
            'resumen': 'Resumen E2E',
            'contenido': 'Contenido completo E2E.',
            'categoria': self.categoria.pk,
            'estado': 'BORRADOR',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        pub_id = resp.data['id']

        # 2. Verificar que NO aparece en API publica
        resp = self.client.get('/api/publicaciones/publicas/')
        titulos = [p['titulo'] for p in resp.data.get('results', resp.data)]
        self.assertNotIn('Articulo E2E', titulos)

        # 3. Publicar
        resp = self.client.post(f'/api/publicaciones/publicaciones/{pub_id}/publicar/')
        self.assertEqual(resp.status_code, 200)

        # 4. Verificar que SÍ aparece en API publica
        resp = self.client.get('/api/publicaciones/publicas/')
        titulos = [p['titulo'] for p in resp.data.get('results', resp.data)]
        self.assertIn('Articulo E2E', titulos)

        # 5. Archivar
        resp = self.client.post(f'/api/publicaciones/publicaciones/{pub_id}/archivar/')
        self.assertEqual(resp.status_code, 200)

        # 6. Verificar que SIGUE visible como Completado (ARCHIVADA en portal)
        resp = self.client.get('/api/publicaciones/publicas/')
        por_id = {p['id']: p for p in resp.data.get('results', resp.data)}
        self.assertIn(pub_id, por_id)
        self.assertEqual(por_id[pub_id]['estado'], 'ARCHIVADA')


# ======================================================================
# Flujo E2E Integrado: Comentario + Moderacion
# ======================================================================


class FlujoCompletoComentarioTest(TestCase):
    """E2E: Login -> Crear comentario -> Moderacion -> Visible publicamente."""

    def setUp(self):
        self.client = APIClient()
        self.staff = crear_staff()
        self.user = crear_usuario()
        self.pub = crear_publicacion(estado=Publicacion.Estado.PUBLICADA)

    def test_flujo_completo_comentario(self):
        # 1. Usuario autenticado crea comentario
        self.client.force_authenticate(user=self.user)
        resp = self.client.post('/api/comentarios/', {
            'publicacion': self.pub.pk,
            'contenido': 'Muy interesante articulo',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        comentario_id = resp.data['id']
        self.assertEqual(resp.data['estado'], 'PENDIENTE')

        # 2. No visible publicamente aun
        self.client.force_authenticate(user=None)
        resp = self.client.get('/api/comentarios/publicos/', {'publicacion_id': self.pub.pk})
        contenidos = [c['contenido'] for c in resp.data]
        self.assertNotIn('Muy interesante articulo', contenidos)

        # 3. Staff aprueba
        self.client.force_authenticate(user=self.staff)
        resp = self.client.patch(f'/api/comentarios/{comentario_id}/aprobar/')
        self.assertEqual(resp.status_code, 200)

        # 4. Ahora visible publicamente
        self.client.force_authenticate(user=None)
        resp = self.client.get('/api/comentarios/publicos/', {'publicacion_id': self.pub.pk})
        contenidos = [c['contenido'] for c in resp.data]
        self.assertIn('Muy interesante articulo', contenidos)


# ======================================================================
# CU-19: Mis Proyectos (usuario propone, admin acepta/declina)
# ======================================================================


class CU19_MisProyectosTest(TestCase):
    """CU-19: Usuario autenticado crea propuestas propias; admin las acepta o declina."""

    def setUp(self):
        self.client = APIClient()
        self.user = crear_usuario()
        self.otro = crear_usuario()
        self.staff = crear_staff()
        self.categoria = crear_categoria()
        self.client.force_authenticate(user=self.user)

    def _crear(self, **kwargs):
        datos = {
            'titulo': 'Mi propuesta',
            'contenido': 'Contenido de la propuesta.',
            'categoria': self.categoria.pk,
            'estado': 'BORRADOR',
        }
        datos.update(kwargs)
        return self.client.post('/api/publicaciones/publicaciones/', datos, format='json')

    def test_usuario_crea_borrador_propio(self):
        resp = self._crear()
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['estado'], 'BORRADOR')
        pub = Publicacion.objects.get(pk=resp.data['id'])
        self.assertEqual(pub.usuario, self.user)

    def test_usuario_no_puede_auto_publicar(self):
        resp = self._crear(estado='PUBLICADA')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['estado'], 'EN_REVISION')

    def test_usuario_solo_ve_las_suyas(self):
        mia = self._crear(titulo='Propuesta mia').data['id']
        crear_publicacion(titulo='Propuesta ajena', usuario=self.otro)
        resp = self.client.get('/api/publicaciones/publicaciones/')
        ids = [p['id'] for p in resp.data.get('results', resp.data)]
        self.assertIn(mia, ids)
        self.assertEqual(len(ids), 1)

    def test_usuario_no_ve_detalle_ajeno(self):
        ajena = crear_publicacion(titulo='Ajeno', usuario=self.otro)
        resp = self.client.get(f'/api/publicaciones/publicaciones/{ajena.pk}/')
        self.assertEqual(resp.status_code, 404)

    def test_usuario_no_publica_ni_archiva(self):
        pub_id = self._crear().data['id']
        self.assertEqual(
            self.client.post(f'/api/publicaciones/publicaciones/{pub_id}/publicar/').status_code, 403
        )
        self.assertEqual(
            self.client.post(f'/api/publicaciones/publicaciones/{pub_id}/archivar/').status_code, 403
        )

    def test_flujo_enviar_revision_y_aceptar(self):
        pub_id = self._crear().data['id']
        resp = self.client.post(f'/api/publicaciones/publicaciones/{pub_id}/enviar-revision/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['estado'], 'EN_REVISION')
        # Admin acepta
        self.client.force_authenticate(user=self.staff)
        resp = self.client.post(f'/api/publicaciones/publicaciones/{pub_id}/publicar/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['estado'], 'PUBLICADA')

    def test_flujo_enviar_revision_y_declinar(self):
        pub_id = self._crear().data['id']
        self.client.post(f'/api/publicaciones/publicaciones/{pub_id}/enviar-revision/')
        # Admin declina (vuelve a borrador)
        self.client.force_authenticate(user=self.staff)
        resp = self.client.post(f'/api/publicaciones/publicaciones/{pub_id}/despublicar/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['estado'], 'BORRADOR')

    def test_anonimo_no_gestiona(self):
        client = APIClient()
        resp = client.get('/api/publicaciones/publicaciones/')
        self.assertIn(resp.status_code, [401, 403])


# ======================================================================
# CU-20: Login con correo y logout
# ======================================================================


class CU20_LoginLogoutTest(TestCase):
    """CU-20: Login acepta usuario o correo; logout cierra sesion."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            'loginuser', 'login@test.com', 'Password123!'
        )

    def test_login_con_username(self):
        resp = self.client.post('/api/auth/login/', {
            'username': 'loginuser', 'password': 'Password123!',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['username'], 'loginuser')

    def test_login_con_email(self):
        resp = self.client.post('/api/auth/login/', {
            'username': 'login@test.com', 'password': 'Password123!',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['username'], 'loginuser')

    def test_login_invalido_401(self):
        resp = self.client.post('/api/auth/login/', {
            'username': 'loginuser', 'password': 'ClaveMala',
        }, format='json')
        self.assertEqual(resp.status_code, 401)

    def test_logout(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post('/api/auth/logout/')
        self.assertEqual(resp.status_code, 200)


# ======================================================================
# CU-21: Solicitudes / PQRSD
# ======================================================================


class CU21_SolicitudesTest(TestCase):
    """CU-21: Visitante crea solicitud; solo staff la gestiona."""

    def setUp(self):
        self.client = APIClient()
        self.staff = crear_staff()

    def test_visitante_crea_solicitud(self):
        resp = self.client.post('/api/solicitudes/nueva/', {
            'tipo': 'QUEJA',
            'nombre': 'Pedro Gomez',
            'email': 'pedro@test.com',
            'telefono': '3001112233',
            'asunto': 'Falta respuesta',
            'mensaje': 'Sin respuesta a mi consulta.',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        from apps.solicitudes.models import Solicitud
        sol = Solicitud.objects.get(pk=resp.data['id'])
        self.assertEqual(sol.estado, Solicitud.Estado.RECIBIDA)
        self.assertEqual(sol.telefono, '3001112233')

    def test_anonimo_no_lista_solicitudes(self):
        resp = self.client.get('/api/solicitudes/')
        self.assertIn(resp.status_code, [401, 403])

    def test_staff_gestiona_solicitud(self):
        self.client.post('/api/solicitudes/nueva/', {
            'nombre': 'Ana', 'email': 'ana@test.com',
            'asunto': 'Ayuda', 'mensaje': 'Necesito ayuda.',
        }, format='json')
        self.client.force_authenticate(user=self.staff)
        resp = self.client.get('/api/solicitudes/')
        self.assertEqual(resp.status_code, 200)
        sol_id = resp.data[0]['id']
        resp = self.client.patch(f'/api/solicitudes/{sol_id}/', {'estado': 'RESUELTA'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['estado'], 'RESUELTA')


# ======================================================================
# CU-22: Imagenes en almacenamiento local
# ======================================================================


class CU22_ImagenesLocalesTest(TestCase):
    """CU-22: Subida local de imagenes (ruta /media/), limite 10MB y borrado fisico."""

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self._override = override_settings(MEDIA_ROOT=self._tmp.name)
        self._override.enable()
        self.addCleanup(self._override.disable)
        self.addCleanup(self._tmp.cleanup)
        self.client = APIClient()
        self.staff = crear_staff()
        self.pub = crear_publicacion(usuario=self.staff)
        self.client.force_authenticate(user=self.staff)
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.png = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
            b'\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        self.SimpleUploadedFile = SimpleUploadedFile

    def test_subir_imagen_local(self):
        archivo = self.SimpleUploadedFile('portada.png', self.png, content_type='image/png')
        resp = self.client.post('/api/imagenes/imagenes/', {
            'archivo': archivo, 'publicacion': self.pub.pk, 'nombre': 'Portada',
        }, format='multipart')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.data['ruta'].startswith('/media/'))
        from apps.imagenes.models import Imagen
        self.assertEqual(Imagen.objects.count(), 1)

    def test_rechaza_mayor_10mb(self):
        grande = self.SimpleUploadedFile('g.jpg', b'x' * (11 * 1024 * 1024), content_type='image/jpeg')
        resp = self.client.post('/api/imagenes/imagenes/', {
            'archivo': grande, 'publicacion': self.pub.pk, 'nombre': 'Grande',
        }, format='multipart')
        self.assertEqual(resp.status_code, 400)

    def test_usuario_solo_sube_a_las_suyas(self):
        otro = crear_publicacion(titulo='Ajena')
        user = crear_usuario()
        self.client.force_authenticate(user=user)
        archivo = self.SimpleUploadedFile('a.png', self.png, content_type='image/png')
        resp = self.client.post('/api/imagenes/imagenes/', {
            'archivo': archivo, 'publicacion': otro.pk, 'nombre': 'Ajena',
        }, format='multipart')
        self.assertEqual(resp.status_code, 403)
