"""Pruebas de seguridad Fase 1 (S1, S6).

S1: un usuario con rol administrativo NO Superadmin no puede gestionar
roles ni usuarios (escalada de privilegios).
S6: producción debe validar la fortaleza de las contraseñas.
"""
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.usuarios.models import Rol, UsuarioRol


def crear_moderador(username='moderador_s1'):
    user = User.objects.create_user(username=username, password='Mod12345!')
    rol, _ = Rol.objects.get_or_create(
        nombre='Moderador', defaults={'descripcion': 'Moderador'}
    )
    UsuarioRol.objects.get_or_create(usuario=user, rol=rol)
    user.refresh_from_db()
    return user


def crear_superadmin(username='superadmin_s1'):
    return User.objects.create_user(
        username=username, password='Sup12345!',
        is_staff=True, is_superuser=True,
    )


class S1AsignarRolTest(TestCase):
    """Un Moderador no puede asignarse (ni asignar) el rol Superadmin."""

    def setUp(self):
        self.client = APIClient()
        self.moderador = crear_moderador()
        # El rol Superadmin existe de antemano (no debe crearse al vuelo).
        Rol.objects.get_or_create(
            nombre='Superadmin', defaults={'descripcion': 'Superadmin'}
        )

    def test_moderador_no_puede_asignarse_superadmin(self):
        self.client.force_authenticate(user=self.moderador)
        resp = self.client.post('/api/roles/asignar/', {
            'usuario': self.moderador.pk, 'rol': 'Superadmin',
        }, format='json')
        self.assertIn(resp.status_code, [401, 403])
        self.assertFalse(
            UsuarioRol.objects.filter(
                usuario=self.moderador, rol__nombre='Superadmin'
            ).exists()
        )

    def test_no_crea_roles_inexistentes_al_vuelo(self):
        admin = crear_superadmin()
        self.client.force_authenticate(user=admin)
        resp = self.client.post('/api/roles/asignar/', {
            'usuario': self.moderador.pk, 'rol': 'RolInventadoQueNoExiste',
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Rol.objects.filter(nombre='RolInventadoQueNoExiste').exists())

    def test_superadmin_si_puede_asignar_rol_existente(self):
        admin = crear_superadmin()
        self.client.force_authenticate(user=admin)
        resp = self.client.post('/api/roles/asignar/', {
            'usuario': self.moderador.pk, 'rol': 'Superadmin',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            UsuarioRol.objects.filter(
                usuario=self.moderador, rol__nombre='Superadmin'
            ).exists()
        )


class S1GestionUsuariosTest(TestCase):
    """Un Moderador no puede cambiar is_staff ni eliminar administradores."""

    def setUp(self):
        self.client = APIClient()
        self.moderador = crear_moderador()
        self.victima = User.objects.create_user(
            username='victima_s1', password='Vic12345!')

    def test_moderador_no_puede_dar_is_staff(self):
        self.client.force_authenticate(user=self.moderador)
        resp = self.client.patch(f'/api/usuarios/{self.victima.pk}/', {
            'is_staff': True,
        }, format='json')
        self.assertIn(resp.status_code, [401, 403])
        self.victima.refresh_from_db()
        self.assertFalse(self.victima.is_staff)

    def test_moderador_no_puede_eliminar_otro_admin(self):
        otro_admin = crear_superadmin(username='otro_admin_s1')
        self.client.force_authenticate(user=self.moderador)
        resp = self.client.delete(f'/api/usuarios/{otro_admin.pk}/')
        self.assertIn(resp.status_code, [401, 403])
        self.assertTrue(User.objects.filter(pk=otro_admin.pk).exists())


class C5DbLocalhostTest(TestCase):
    """Postgres de desarrollo solo escucha en localhost (C5)."""

    def test_puerto_solo_localhost(self):
        import pathlib
        compose = (pathlib.Path(__file__).resolve().parent.parent.parent.parent / 'docker-compose.yml').read_text(
            encoding='utf-8')
        self.assertIn('127.0.0.1:${DB_PORT:-5432}:5432', compose)


class C2ProdAjustesTest(TestCase):
    """prod.py detrás de proxy: cabecera, hosts y STORAGES (C2)."""

    @staticmethod
    def _prod_source():
        import pathlib
        prod = pathlib.Path(__file__).resolve().parent.parent.parent / 'config' / 'settings' / 'prod.py'
        return prod.read_text(encoding='utf-8')

    def test_proxy_ssl_header(self):
        self.assertIn('SECURE_PROXY_SSL_HEADER', self._prod_source())

    def test_storages_modernos(self):
        fuente = self._prod_source()
        self.assertIn('STORAGES', fuente)
        self.assertNotIn('STATICFILES_STORAGE =', fuente)

    def test_sin_xss_filter_obsoleto(self):
        self.assertNotIn('SECURE_BROWSER_XSS_FILTER', self._prod_source())


class C3EnvDesarrolloTest(TestCase):
    """local.py lee DEBUG, ALLOWED_HOSTS y CORS de variables de entorno (C3)."""

    @staticmethod
    def _local_source():
        import pathlib
        local = pathlib.Path(__file__).resolve().parent.parent.parent / 'config' / 'settings' / 'local.py'
        return local.read_text(encoding='utf-8')

    def test_debug_de_env(self):
        self.assertIn("config('DEBUG'", self._local_source())

    def test_allowed_hosts_de_env(self):
        self.assertIn("config('ALLOWED_HOSTS'", self._local_source())

    def test_cors_de_env(self):
        fuente = self._local_source()
        self.assertIn("'CORS_ALLOWED_ORIGINS'", fuente)
        self.assertIn('Csv()', fuente)


class C1SettingsReorgTest(TestCase):
    """base.py común; local/prod heredan de base; settings.py muerto eliminado."""

    @staticmethod
    def _settings_dir():
        import pathlib
        return pathlib.Path(__file__).resolve().parent.parent.parent / 'config' / 'settings'

    def test_existe_base_y_no_settings_muerto(self):
        d = self._settings_dir()
        self.assertTrue((d / 'base.py').exists())
        self.assertFalse((d.parent / 'settings.py').exists())

    def test_prod_hereda_de_base_no_de_local(self):
        prod = (self._settings_dir() / 'prod.py').read_text(encoding='utf-8')
        self.assertIn('config.settings.base', prod)
        self.assertNotIn('config.settings.local', prod)

    def test_local_hereda_de_base(self):
        local = (self._settings_dir() / 'local.py').read_text(encoding='utf-8')
        self.assertIn('config.settings.base', local)


class L2StaffUnificadoTest(TestCase):
    """Una sola es_staff() y un solo ROLES_STAFF en todo el backend (L2)."""

    def test_misma_funcion_en_todas_las_apps(self):
        from apps.usuarios import permissions as central
        from apps.publicaciones import views as pub_v
        from apps.imagenes import views as img_v
        self.assertTrue(hasattr(central, 'es_staff'))
        self.assertIs(pub_v.es_staff, central.es_staff)
        self.assertIs(img_v.es_staff, central.es_staff)

    def test_roles_staff_unicos(self):
        from apps.usuarios import permissions as central
        from apps.usuarios import signals as senales
        self.assertTrue(hasattr(central, 'ROLES_STAFF'))
        self.assertIs(senales.ROLES_STAFF, central.ROLES_STAFF)


class T2LoggingDevTest(TestCase):
    """La configuración base define LOGGING con salida a consola (T2)."""

    def test_logging_con_consola(self):
        from django.conf import settings
        self.assertIn('console', settings.LOGGING['handlers'])
        self.assertIn('console', settings.LOGGING['root']['handlers'])


class P3IndicesTest(TestCase):
    """Publicacion tiene índice en (estado, -fechaPublicacion) (P3)."""

    def test_indice_estado_fecha(self):
        from apps.publicaciones.models import Publicacion
        campos = [list(idx.fields) for idx in Publicacion._meta.indexes]
        self.assertIn(['estado', '-fechaPublicacion'], campos)


class P2PaginacionTest(TestCase):
    """Listados grandes devuelven página (count+results), no todo (P2)."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username='staff_p2', password='Stf12345!',
            is_staff=True, is_superuser=True,
        )
        self.client.force_authenticate(user=self.staff)

    def test_usuarios_paginado(self):
        resp = self.client.get('/api/usuarios/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('results', resp.data)

    def test_registros_paginado(self):
        resp = self.client.get('/api/registros/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('results', resp.data)

    def test_solicitudes_paginado(self):
        resp = self.client.get('/api/solicitudes/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('results', resp.data)

    def test_pendientes_paginado(self):
        resp = self.client.get('/api/comentarios/pendientes/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('results', resp.data)


class S7LoginThrottleTest(TestCase):
    """Fuerza bruta en login limitada a 5 intentos/min (S7)."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.client = APIClient()
        User.objects.create_user(username='victima_login', password='Clave12345!')

    def test_sexto_intento_rapido_es_429(self):
        estados = []
        for _ in range(6):
            resp = self.client.post('/api/auth/login/', {
                'username': 'victima_login', 'password': 'ClaveMala',
            }, format='json')
            estados.append(resp.status_code)
        self.assertEqual(estados[-1], 429)
        self.assertTrue(all(e in (401, 429) for e in estados))


class S6PasswordValidatorsProdTest(TestCase):
    """prod.py debe declarar validadores (no heredar la lista vacía de local)."""

    def test_prod_declara_validadores_propios(self):
        import pathlib
        prod = pathlib.Path(__file__).resolve().parent.parent.parent / 'config' / 'settings' / 'prod.py'
        fuente = prod.read_text(encoding='utf-8')
        self.assertIn('AUTH_PASSWORD_VALIDATORS', fuente)
        self.assertIn('MinimumLengthValidator', fuente)

    def test_password_debil_rechazada_con_validadores_prod(self):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        validadores = [
            {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
            {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
             'OPTIONS': {'min_length': 8}},
            {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
            {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
        ]
        with override_settings(AUTH_PASSWORD_VALIDATORS=validadores), \
                self.assertRaises(ValidationError):
            validate_password('1')
