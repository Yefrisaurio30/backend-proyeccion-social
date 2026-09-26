# Plan de tareas — BACKEND (fraccionado)

Cada tarea del Kanban corresponde a **1 rama `feature/*`** creada desde `develop`,
un PR hacia `develop`, y una entrada en el board. Orden de dependencia abajo.

> Pendiente: recuerda crear la rama `develop` una sola vez (ver `docs/GIT_FLOW.md`).

## Tareas (en orden de ejecución)

### 1. Base del backend — `feature/base-django`
- Archivos: `manage.py`, `requirements.txt`, `Procfile`, `runtime.txt`, `config/`
- Issue: *"Base del backend: configuración Django, dependencias y deploy"*
- Commits sugeridos:
  - `chore: requirements, Procfile y runtime`
  - `feat(config): settings local/prod, urls y wsgi`
- Verificación: `python manage.py check`

### 2. Módulo Usuarios — `feature/modulo-usuarios`
- Archivos: `apps/usuarios/`
- Issue: *"Modelo de usuarios con auth, roles y permisos (login/registro)"*
- Commits sugeridos:
  - `feat(usuarios): modelos, migraciones y serializers`
  - `feat(usuarios): vistas auth y asignación de roles`
- Dependencia: base (#1)

### 3. Módulo Publicaciones — `feature/modulo-publicaciones`
- Archivos: `apps/publicaciones/`
- Issue: *"CRUD de publicaciones con estados, filtros y categorías/programas"*
- Commits sugeridos:
  - `feat(publicaciones): modelo y migraciones`
  - `feat(publicaciones): serializers, filtros y vistas públicas/admin`
- Dependencia: usuarios (#2)

### 4. Módulo Comentarios — `feature/modulo-comentarios`
- Archivos: `apps/comentarios/`
- Issue: *"Comentarios y moderación (aprobar/rechazar)"*
- Dependencia: publicaciones (#3)

### 5. Módulo Solicitudes — `feature/modulo-solicitudes`
- Archivos: `apps/solicitudes/`
- Issue: *"Flujo de solicitudes de proyectos sociales"*
- Dependencia: publicaciones (#3)

### 6. Módulo Imágenes — `feature/modulo-imagenes`
- Archivos: `apps/imagenes/`
- Issue: *"Galería y subida de imágenes (local/Supabase)"*
- Dependencia: publicaciones (#3)

### 7. Módulo Reportes — `feature/modulo-reportes`
- Archivos: `apps/reportes/`
- Issue: *"Reportes y estadísticas del panel"*
- Dependencia: publicaciones (#3)

### 8. Actividad / Trazabilidad — `feature/actividad-trazabilidad`
- Archivos: `apps/actividad/`
- Issue: *"Registro de actividad y trazabilidad de cambios"*
- Dependencia: usuarios (#2)

### 9. Datos de demostración — `feature/datos-demo`
- Archivos: `seed_demo.py`
- Issue: *"Script de datos demo para desarrollo"*
- Commits sugeridos:
  - `feat(seed): usuario de pruebas y publicaciones demo`
- Dependencia: todas (#2–#8)

## Imports/¿qué se excluye?

- `.gitignore` ya excluye: `.env`, `media/`, `__pycache__/`, `.venv/`.
- **No** subir nunca tu `backend/.env` (credenciales).
- Las imágenes locales (`media/`) no versionar: se generan o se suben por otro medio.

## Checklist final por tarea

- [ ] Rama creada desde `develop` (`git switch -c feature/... develop`)
- [ ] Commits fraccionados con mensajes claros
- [ ] `push -u origin feature/...`
- [ ] PR abierto hacia `develop` en GitHub
- [ ] PR aprobado/mergado → mover issue a **Done** en el Kanban
- [ ] `git switch develop && git pull origin develop`