# -*- coding: utf-8 -*-
"""
Datos de demostracion - Sistema de Proyeccion Social UNIMINUTO.
Idempotente: usa get_or_create, se puede ejecutar cuantas veces sea.
Uso: python seed_demo.py  (con DJANGO_SETTINGS_MODULE=config.settings.local)
"""
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth.models import User  # noqa: E402
from apps.publicaciones.models import Publicacion, Categoria  # noqa: E402

CARRERAS = [
    'Tecnología en Comunicación Gráfica',
    'Tecnología en Desarrollo de Software',
    'Trabajo Social',
    'Administración de Empresas',
    'Administración en Seguridad y Salud en el Trabajo',
    'Administración Financiera',
    'Comunicación Social - Periodismo',
    'Comunicación Visual',
    'Contaduría Pública',
    'Ingeniería Agroecológica',
    'Licenciatura en Educación Infantil',
    'Psicología',
]

PUBLICACIONES = [
    ('IA en la Educacion', 'IA en educacion',
     'Tecnología en Desarrollo de Software', 'PUBLICADA'),
    ('Hackathon 2026', 'Innovacion',
     'Tecnología en Desarrollo de Software', 'PUBLICADA'),
    ('Reforestacion', 'Sabana',
     'Ingeniería Agroecológica', 'PUBLICADA'),
    ('Ciberseguridad', 'Seguridad',
     'Tecnología en Desarrollo de Software', 'BORRADOR'),
    ('Jornada Salud', 'Rural',
     'Psicología', 'ARCHIVADA'),
    ('Voluntariado', 'Comunidad',
     'Trabajo Social', 'PUBLICADA'),
]


def main():
    admin = User.objects.get(username='admin')
    cats = {}
    for nombre in CARRERAS:
        cat, _ = Categoria.objects.get_or_create(
            nombre=nombre, defaults={'descripcion': nombre}
        )
        cats[nombre] = cat

    for titulo, resumen, carrera, estado in PUBLICACIONES:
        Publicacion.objects.get_or_create(
            titulo=titulo,
            defaults={
                'resumen': resumen,
                'contenido': f'Contenido de {titulo}',
                'estado': estado,
                'categoria': cats[carrera],
                'usuario': admin,
            },
        )

    for titulo, _, _, _ in PUBLICACIONES:
        pub = Publicacion.objects.get(titulo=titulo)
        if pub.estado == 'PUBLICADA' and pub.fechaPublicacion is None:
            pub.publicar()

    print(f'Datos: {Publicacion.objects.count()} pubs, {Categoria.objects.count()} cats')


if __name__ == '__main__':
    main()
