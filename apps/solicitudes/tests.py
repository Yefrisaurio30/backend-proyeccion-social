"""Pruebas Fase 2 (S7): el formulario público de solicitudes tiene throttle."""
from django.test import TestCase
from rest_framework.test import APIClient


class S7SolicitudesThrottleTest(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.client = APIClient()

    def _nueva(self, i):
        return self.client.post('/api/solicitudes/nueva/', {
            'tipo': 'QUEJA',
            'nombre': f'Spam {i}',
            'email': f'spam{i}@test.com',
            'asunto': 'Spam',
            'mensaje': 'Mensaje de spam.',
        }, format='json')

    def test_rafaga_anonima_es_limitada(self):
        estados = [self._nueva(i).status_code for i in range(61)]
        self.assertEqual(estados[-1], 429)
        self.assertIn(201, estados)
