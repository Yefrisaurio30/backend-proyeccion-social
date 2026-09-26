# Git Flow — Guía del repositorio

Este repo usa **Git Flow**: un modelo de ramas para integrar trabajo en equipo
sin pisarse. Aquí está explicado simple para aplicarlo a las tareas del Kanban.

## Modelo de ramas

| Rama            | Uso                                                        | ¿Se hace push directo? |
|-----------------|------------------------------------------------------------|------------------------|
| `main`          | Código de producción, siempre funcional                    | NO (solo vía PR)       |
| `develop`       | Integración de todo el trabajo en desarrollo               | NO (solo vía PR)       |
| `feature/*`     | Una por cada tarea del Kanban. Se crea desde `develop`     | SÍ (para PR)           |
| `release/*`     | Preparar una versión formal (v1.0) y pasar a `main`        | SÍ (para PR)           |
| `hotfix/*`      | Arreglo URGENTE de producción. Se crea desde `main`        | SÍ (para PR)           |

Reglas de oro:

1. **Nunca** se commitea ni a `main` ni a `develop` directamente.
2. Cada tarea del Kanban = una rama `feature/<tarea>`.
3. La rama se sube y se abre un **Pull Request (PR)** hacia `develop`.
4. `main` solo recibe código vía `release/*` (o `hotfix/*`).
5. Nombres de ramas: `feature/nombre-corto`, separar palabras con `-`.

## Ciclo ideal (por tarea del Kanban)

```
1. Mantener tu develop actualizada
   git switch develop
   git pull origin develop

2. Crear la rama de la tarea
   git switch -c feature/modulo-usuarios develop

3. Hacer los commits fraccionados de la tarea
   git add apps/usuarios
   git commit -m "feat(usuarios): modelo y migraciones"
   git add apps/usuarios/serializers.py
   git commit -m "feat(usuarios): serializers y vistas"
   ...

4. Subir y abrir PR
   git push -u origin feature/modulo-usuarios
   # En GitHub: New Pull Request → base: develop ← compare: feature/modulo-usuarios

5. Cerrar la tarea en el Kanban (issue → Done)
```

## Cheatsheet completo

```bash
# ---- PRIMERA VEZ (una sola vez) ----
git switch main
git pull origin main
git branch develop                    # crea la rama de integración
git push origin develop
# Proteger main/develop en GitHub: Settings → Branches → Require PR

# ---- FLUJO NORMAL ----
git switch develop && git pull origin develop      # actualizar
git switch -c feature/nombre-tarea develop         # rama de tarea
# ...trabajar y commitear...
git add .
git commit -m "feat(area): descripcion corta"
git push -u origin feature/nombre-tarea            # subir (se abre PR)
git switch develop                                 # volver a la integración
git pull origin develop                            # traer lo que se integró
git merge feature/nombre-tarea --no-ff             # merge local (tras aprobar PR)
git push origin develop

# ---- RELEASE / VERSIÓN ----
git switch -c release/v1.0 develop
git push -u origin release/v1.0                    # PR release → main (y a develop)
git switch main && git pull origin main
git tag v1.0.0 && git push origin v1.0.0           # marcar versión publicada

# ---- HOTFIX (urgencia en producción) ----
git switch -c hotfix/arreglo-login main
# ...arreglo...
git commit -m "fix(auth): error de sesion"
git push -u origin hotfix/arreglo-login            # PR hotfix → main y → develop

# ---- BORRAR RAMAS TERMINADAS ----
git branch -d feature/nombre-tarea
git push origin --delete feature/nombre-tarea
```

## Mensajes de commit

Formato recomendado: `tipo(area): descripcion`

| Tipo  | Cuándo         | Ejemplo |
|-------|----------------|---------|
| feat  | Nueva función  | `feat(auth): login con sesion persistente` |
| fix   | Corrección     | `fix(publicaciones): filtro por programa` |
| chore | Infraestructura | `chore: actualizar requirements` |
| docs  | Documentación  | `docs: agregar git flow` |