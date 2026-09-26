-- ==============================================================
-- ROW LEVEL SECURITY (RLS) — Tabla 'comentario'
-- Sistema de Proyeccion Social UNIMINUTO
--
-- Ejecutar en la consola SQL de Supabase (Dashboard > SQL Editor)
-- ==============================================================

-- 1. Habilitar RLS en la tabla comentario
ALTER TABLE comentario ENABLE ROW LEVEL SECURITY;

-- 2. Politica SELECT publica: solo comentarios APROBADO son visibles
--    Cualquier visitante (anonimo o autenticado) puede leer.
CREATE POLICY "comentarios_aprobados_select_publico"
  ON comentario
  FOR SELECT
  USING (estado = 'APROBADO');

-- 3. Politica SELECT solo si la publicacion asociada esta PUBLICADA
--    Refuerza que no se pueda espiar contenido de borradores.
CREATE POLICY "comentarios_select_publicacion_publicada"
  ON comentario
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1
      FROM publicacion
      WHERE publicacion.id = comentario.publicacion_id
        AND publicacion.estado = 'PUBLICADA'
    )
  );

-- 4. Politica INSERT: usuarios autenticados pueden crear comentarios
--    El estado siempre se fuerza a PENDIENTE en el backend (RN-03).
CREATE POLICY "comentarios_insert_autenticado"
  ON comentario
  FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() IS NOT NULL);

-- 5. Politica UPDATE: solo staff/moderadores pueden modificar estado
--    (aprobar/rechazar). Esto es redundante con el backend pero
--    protege contra acceso directo a la tabla.
CREATE POLICY "comentarios_update_staff"
  ON comentario
  FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1
      FROM auth.users
      WHERE auth.uid() = id
        AND (
          raw_user_meta_data ->> 'is_staff' = 'true'
          OR raw_user_meta_data ->> 'is_superuser' = 'true'
        )
    )
  )
  WITH CHECK (true);
