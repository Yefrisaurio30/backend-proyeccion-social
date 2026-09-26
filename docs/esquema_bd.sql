-- =============================================================================
-- SISTEMA DE PROYECCION SOCIAL UNIMINUTO
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. USUARIO (tabla auth_user de Django - simplificada a campos usados)
-- -----------------------------------------------------------------------------
CREATE TABLE auth_user (
    id              SERIAL PRIMARY KEY,
    password        VARCHAR(128) NOT NULL,             -- hash, nunca en claro
    last_login      TIMESTAMPTZ NULL,
    is_superuser    BOOLEAN NOT NULL DEFAULT FALSE,
    username        VARCHAR(150) NOT NULL UNIQUE,
    first_name      VARCHAR(150) NOT NULL DEFAULT '',
    last_name       VARCHAR(150) NOT NULL DEFAULT '',
    email           VARCHAR(254) NOT NULL DEFAULT '',
    is_staff        BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX auth_user_username_idx ON auth_user (username);

-- -----------------------------------------------------------------------------
-- 1b. PERFIL DE USUARIO (tabla usuarios_perfil) - afiliacion del registro
-- -----------------------------------------------------------------------------
CREATE TABLE usuarios_perfil (
    id               SERIAL PRIMARY KEY,
    tipo_afiliacion  VARCHAR(20) NOT NULL DEFAULT 'COMUNIDAD',
    telefono         VARCHAR(30) NOT NULL DEFAULT '',
    usuario_id       INTEGER NOT NULL UNIQUE,
    CONSTRAINT chk_perfil_tipo CHECK (tipo_afiliacion IN (
        'ESTUDIANTE', 'DOCENTE', 'ADMINISTRATIVO', 'COMUNIDAD', 'ALIADO'
    )),
    CONSTRAINT fk_perfil_usuario FOREIGN KEY (usuario_id)
        REFERENCES auth_user (id) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- 2. CATEGORIA (tabla publicaciones_categoria)
-- -----------------------------------------------------------------------------
CREATE TABLE publicaciones_categoria (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT NOT NULL DEFAULT ''
);

-- -----------------------------------------------------------------------------
-- 3. PUBLICACION (tabla publicaciones_publicacion)
-- -----------------------------------------------------------------------------
CREATE TABLE publicaciones_publicacion (
    id               SERIAL PRIMARY KEY,
    titulo           VARCHAR(200) NOT NULL,
    resumen          TEXT NOT NULL DEFAULT '',                    -- max 500
    contenido        TEXT NOT NULL,
    estado           VARCHAR(20) NOT NULL DEFAULT 'BORRADOR',
    "fechaCreacion"  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "fechaPublicacion" TIMESTAMPTZ NULL,
    categoria_id     INTEGER NOT NULL,
    usuario_id       INTEGER NOT NULL,
    vistas           INTEGER NOT NULL DEFAULT 0,
    programa_nombre      VARCHAR(200) NOT NULL DEFAULT '',
    programa_codigo      VARCHAR(50) NOT NULL DEFAULT '',
    coordinador_nombre   VARCHAR(200) NOT NULL DEFAULT '',
    coordinador_email    VARCHAR(254) NOT NULL DEFAULT '',
    sede                 VARCHAR(100) NOT NULL DEFAULT '',
    fecha_inicio     DATE NULL,
    fecha_fin        DATE NULL,
    beneficiarios    INTEGER NULL,
    ubicacion        VARCHAR(200) NOT NULL DEFAULT '',
    investigador     VARCHAR(200) NOT NULL DEFAULT '',
    etiquetas        VARCHAR(500) NOT NULL DEFAULT '',            -- tags separados por coma
    -- Restriccion de estado (enumeracion del modelo)
    CONSTRAINT chk_publicacion_estado CHECK (estado IN ('BORRADOR', 'EN_REVISION', 'PUBLICADA', 'ARCHIVADA')),
    CONSTRAINT fk_publicacion_categoria FOREIGN KEY (categoria_id)
        REFERENCES publicaciones_categoria (id) ON DELETE PROTECT,
    CONSTRAINT fk_publicacion_usuario FOREIGN KEY (usuario_id)
        REFERENCES auth_user (id) ON DELETE CASCADE
);

-- Indices para busqueda y filtros
CREATE INDEX idx_publicacion_estado ON publicaciones_publicacion (estado);
CREATE INDEX idx_publicacion_categoria ON publicaciones_publicacion (categoria_id);
CREATE INDEX idx_publicacion_fecha ON publicaciones_publicacion ("fechaPublicacion" DESC);
CREATE INDEX idx_publicacion_usuario ON publicaciones_publicacion (usuario_id);

-- -----------------------------------------------------------------------------
-- 4. IMAGEN (tabla imagenes_imagen) - Supabase Storage para archivos
-- -----------------------------------------------------------------------------
CREATE TABLE imagenes_imagen (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(255) NOT NULL,
    ruta            VARCHAR(500) NOT NULL,              -- URL publica Supabase
    descripcion     TEXT NOT NULL DEFAULT '',
    "fechaCarga"    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    publicacion_id  INTEGER NOT NULL,
    CONSTRAINT fk_imagen_publicacion FOREIGN KEY (publicacion_id)
        REFERENCES publicaciones_publicacion (id) ON DELETE CASCADE
);

CREATE INDEX idx_imagen_publicacion ON imagenes_imagen (publicacion_id);

-- -----------------------------------------------------------------------------
-- 5. COMENTARIO (tabla comentarios_comentario)
-- -----------------------------------------------------------------------------
CREATE TABLE comentarios_comentario (
    id                SERIAL PRIMARY KEY,
    contenido         TEXT NOT NULL,                    -- max 2000
    "fechaCreacion"   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    estado            VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    "fechaModeracion" TIMESTAMPTZ NULL,
    "motivoRechazo"   TEXT NOT NULL DEFAULT '',         -- max 500
    publicacion_id    INTEGER NOT NULL,
    usuario_id        INTEGER NOT NULL,
    -- Restriccion de estado del comentario
    CONSTRAINT chk_comentario_estado CHECK (estado IN ('PENDIENTE', 'APROBADO', 'RECHAZADO')),
    CONSTRAINT fk_comentario_publicacion FOREIGN KEY (publicacion_id)
        REFERENCES publicaciones_publicacion (id) ON DELETE CASCADE,
    CONSTRAINT fk_comentario_usuario FOREIGN KEY (usuario_id)
        REFERENCES auth_user (id) ON DELETE CASCADE
);

-- Indices: cola de moderacion y comentarios publicos por publicacion
CREATE INDEX idx_comentario_estado ON comentarios_comentario (estado);
CREATE INDEX idx_comentario_publicacion ON comentarios_comentario (publicacion_id);
CREATE INDEX idx_comentario_usuario ON comentarios_comentario (usuario_id);

-- -----------------------------------------------------------------------------
-- 6. REGISTRO DE ACTIVIDAD / TRAZABILIDAD (tabla actividad_registroactividad)
-- -----------------------------------------------------------------------------
CREATE TABLE actividad_registroactividad (
    id          SERIAL PRIMARY KEY,
    accion      VARCHAR(20) NOT NULL,
    fecha       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    descripcion TEXT NOT NULL,                          -- max 500
    modelo      VARCHAR(50) NOT NULL DEFAULT '',
    objeto_id   INTEGER NULL,
    usuario_id  INTEGER NULL,
    -- Acciones permitidas (enumeracion del modelo)
    CONSTRAINT chk_actividad_accion CHECK (accion IN (
        'CREAR', 'EDITAR', 'ELIMINAR',
        'PUBLICAR', 'DESPUBLICAR', 'ARCHIVAR',
        'APROBADO', 'RECHAZADO',
        'LOGIN', 'LOGOUT'
    )),
    CONSTRAINT fk_actividad_usuario FOREIGN KEY (usuario_id)
        REFERENCES auth_user (id) ON DELETE SET NULL
);

CREATE INDEX idx_actividad_fecha ON actividad_registroactividad (fecha DESC);
CREATE INDEX idx_actividad_usuario ON actividad_registroactividad (usuario_id);
CREATE INDEX idx_actividad_modelo ON actividad_registroactividad (modelo, objeto_id);

-- -----------------------------------------------------------------------------
-- 7. SOLICITUD / PQRSD (tabla solicitudes_solicitud) - portal publico
-- -----------------------------------------------------------------------------
CREATE TABLE solicitudes_solicitud (
    id       SERIAL PRIMARY KEY,
    tipo     VARCHAR(20) NOT NULL DEFAULT 'SOLICITUD',
    nombre   VARCHAR(200) NOT NULL,
    email    VARCHAR(254) NOT NULL,
    telefono VARCHAR(30) NOT NULL DEFAULT '',
    asunto   VARCHAR(300) NOT NULL,
    mensaje  TEXT NOT NULL,
    estado   VARCHAR(20) NOT NULL DEFAULT 'RECIBIDA',
    fecha    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_solicitud_tipo CHECK (tipo IN (
        'SOLICITUD', 'PETICION', 'QUEJA', 'RECLAMO', 'SUGERENCIA'
    )),
    CONSTRAINT chk_solicitud_estado CHECK (estado IN (
        'RECIBIDA', 'EN_PROCESO', 'RESUELTA', 'CERRADA'
    ))
);

CREATE INDEX idx_solicitud_estado ON solicitudes_solicitud (estado);
CREATE INDEX idx_solicitud_fecha ON solicitudes_solicitud (fecha DESC);

-- -----------------------------------------------------------------------------
-- 8. ROL / PERMISO (DER) - RBAC aditivo, capa compatible con is_staff
-- -----------------------------------------------------------------------------
CREATE TABLE usuarios_rol (
    id             BIGSERIAL PRIMARY KEY,
    nombre         VARCHAR(80) NOT NULL UNIQUE,
    descripcion    VARCHAR(250) NOT NULL DEFAULT '',
    "fechaCreacion" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE usuarios_permiso (
    id       BIGSERIAL PRIMARY KEY,
    codename VARCHAR(80) NOT NULL UNIQUE,
    nombre   VARCHAR(120) NOT NULL,
    modulo   VARCHAR(80) NOT NULL DEFAULT ''
);

CREATE TABLE usuarios_rolpermisos (
    id         BIGSERIAL PRIMARY KEY,
    rol_id     BIGINT NOT NULL REFERENCES usuarios_rol(id) ON DELETE CASCADE,
    permiso_id BIGINT NOT NULL REFERENCES usuarios_permiso(id) ON DELETE CASCADE,
    UNIQUE(rol_id, permiso_id)
);

CREATE TABLE usuarios_usuariorol (
    id            BIGSERIAL PRIMARY KEY,
    usuario_id    BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    rol_id        BIGINT NOT NULL REFERENCES usuarios_rol(id) ON DELETE CASCADE,
    asignado_por  BIGINT REFERENCES auth_user(id) ON DELETE SET NULL,
    "fechaCreacion" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(usuario_id, rol_id)
);

-- -----------------------------------------------------------------------------
-- 9. REPORTE (DER) - persistencia de reportes generados
-- -----------------------------------------------------------------------------
CREATE TABLE reportes_reporte (
    id               BIGSERIAL PRIMARY KEY,
    titulo           VARCHAR(200) NOT NULL DEFAULT '',
    tipo             VARCHAR(30) NOT NULL DEFAULT 'GENERAL',
    parametros       JSONB NOT NULL DEFAULT '{}',
    "fechaGeneracion" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    creador_id       BIGINT REFERENCES auth_user(id) ON DELETE SET NULL
);

-- =============================================================================
-- VISTAS UTILIZADAS POR EL DASHBOARD (reportes)
-- =============================================================================

CREATE VIEW vw_publicaciones_por_estado AS
SELECT
    COUNT(*)                                                          AS total,
    COUNT(*) FILTER (WHERE estado = 'BORRADOR')                      AS borradores,
    COUNT(*) FILTER (WHERE estado = 'EN_REVISION')                   AS en_revision,
    COUNT(*) FILTER (WHERE estado = 'PUBLICADA')                     AS publicadas,
    COUNT(*) FILTER (WHERE estado = 'ARCHIVADA')                     AS archivadas
FROM publicaciones_publicacion;

CREATE VIEW vw_comentarios_por_estado AS
SELECT
    COUNT(*)                                                          AS total,
    COUNT(*) FILTER (WHERE estado = 'PENDIENTE')                     AS pendientes,
    COUNT(*) FILTER (WHERE estado = 'APROBADO')                      AS aprobados,
    COUNT(*) FILTER (WHERE estado = 'RECHAZADO')                     AS rechazados
FROM comentarios_comentario;

-- Top 5 publicaciones mas comentadas (usado en Dashboard)
CREATE VIEW vw_publicaciones_mas_comentadas AS
SELECT
    pp.id,
    pp.titulo,
    COUNT(cc.id) AS num_comentarios
FROM publicaciones_publicacion pp
LEFT JOIN comentarios_comentario cc ON cc.publicacion_id = pp.id
GROUP BY pp.id, pp.titulo
HAVING COUNT(cc.id) > 0
ORDER BY num_comentarios DESC
LIMIT 5;

CREATE VIEW vw_solicitudes_por_estado AS
SELECT
    COUNT(*)                                                          AS total,
    COUNT(*) FILTER (WHERE estado = 'RECIBIDA')                       AS recibidas,
    COUNT(*) FILTER (WHERE estado = 'EN_PROCESO')                     AS en_proceso,
    COUNT(*) FILTER (WHERE estado = 'RESUELTA')                       AS resueltas,
    COUNT(*) FILTER (WHERE estado = 'CERRADA')                        AS cerradas
FROM solicitudes_solicitud;

-- =============================================================================
-- DATOS DE PRUEBA (opcional - para desarrollo)
-- =============================================================================

INSERT INTO publicaciones_categoria (nombre, descripcion) VALUES
  ('Tecnología en Comunicación Gráfica', 'Diseño y comunicación visual'),
  ('Tecnología en Desarrollo de Software', 'Software e innovación digital'),
  ('Trabajo Social', 'Intervención y desarrollo comunitario'),
  ('Administración de Empresas', 'Gestión y emprendimiento'),
  ('Administración en Seguridad y Salud en el Trabajo', 'SST y bienestar laboral'),
  ('Administración Financiera', 'Finanzas y contabilidad'),
  ('Comunicación Social - Periodismo', 'Periodismo y medios'),
  ('Comunicación Visual', 'Artes y medios visuales'),
  ('Contaduría Pública', 'Contabilidad e impuestos'),
  ('Ingeniería Agroecológica', 'Agroecología y sostenibilidad'),
  ('Licenciatura en Educación Infantil', 'Primera infancia y pedagogía'),
  ('Psicología', 'Salud mental y comportamiento');

-- Ejemplo: publicacion publicada (para validar el portal)
INSERT INTO publicaciones_publicacion
    (titulo, resumen, contenido, estado, "fechaPublicacion", categoria_id, usuario_id)
VALUES
    ('IA en la Educacion',
     'La inteligencia artificial transforma el aprendizaje',
     'Contenido completo sobre IA aplicada a la educacion...',
     'PUBLICADA', NOW(), 2, 1);