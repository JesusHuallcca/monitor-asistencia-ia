-- =====================================================
-- Monitor Inteligente de Asistencia con IA
-- Esquema integrado: Seguridad + Usuarios + Cursos +
-- Reconocimiento Facial + Asistencia
-- =====================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS asistencias;
DROP TABLE IF EXISTS sesiones_clase;
DROP TABLE IF EXISTS auditoria;
DROP TABLE IF EXISTS rostros;
DROP TABLE IF EXISTS notas;
DROP TABLE IF EXISTS evaluaciones;
DROP TABLE IF EXISTS matriculas;
DROP TABLE IF EXISTS asignaciones_profesor;
DROP TABLE IF EXISTS cursos;
DROP TABLE IF EXISTS estudiantes;
DROP TABLE IF EXISTS profesores;
DROP TABLE IF EXISTS usuarios;

SET FOREIGN_KEY_CHECKS = 1;

-- ---------- USUARIOS ----------
CREATE TABLE usuarios (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    username           VARCHAR(50)  NOT NULL UNIQUE,
    email              VARCHAR(120) NOT NULL UNIQUE,
    password_hash      VARCHAR(255) NOT NULL,
    nombres            VARCHAR(100) NOT NULL,
    apellidos          VARCHAR(100) NOT NULL,
    rol                ENUM('superadmin','admin','profesor','estudiante') NOT NULL,
    estado             ENUM('pendiente','activo','inactivo') NOT NULL DEFAULT 'activo',
    intentos_fallidos  INT NOT NULL DEFAULT 0,
    bloqueado_hasta    DATETIME NULL,
    ultimo_login       DATETIME NULL,
    creado_por         INT NULL,
    creado_en          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_usuarios_creado_por
        FOREIGN KEY (creado_por)
        REFERENCES usuarios(id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------- PROFESORES ----------
CREATE TABLE profesores (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id   INT NOT NULL UNIQUE,
    especialidad VARCHAR(120) NULL,
    telefono     VARCHAR(20) NULL,

    CONSTRAINT fk_profesores_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------- ESTUDIANTES ----------
CREATE TABLE estudiantes (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL UNIQUE,
    codigo     VARCHAR(20) NOT NULL UNIQUE,
    carrera    VARCHAR(120) NULL,
    ciclo      TINYINT NULL,
    telefono   VARCHAR(20) NULL,

    CONSTRAINT fk_estudiantes_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------- CURSOS ----------
CREATE TABLE cursos (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    codigo      VARCHAR(20)  NOT NULL UNIQUE,
    nombre      VARCHAR(150) NOT NULL,
    descripcion TEXT NULL,
    periodo     VARCHAR(20)  NOT NULL,
    activo      TINYINT(1) NOT NULL DEFAULT 1,
    creado_en   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------- PROFESOR <-> CURSO ----------
CREATE TABLE asignaciones_profesor (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    curso_id     INT NOT NULL,
    profesor_id  INT NOT NULL,
    asignado_por INT NULL,
    asignado_en  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_curso_profesor (curso_id, profesor_id),

    CONSTRAINT fk_asig_curso
        FOREIGN KEY (curso_id)
        REFERENCES cursos(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_asig_profesor
        FOREIGN KEY (profesor_id)
        REFERENCES profesores(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_asig_por
        FOREIGN KEY (asignado_por)
        REFERENCES usuarios(id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------- ESTUDIANTE <-> CURSO ----------
CREATE TABLE matriculas (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    curso_id        INT NOT NULL,
    estudiante_id   INT NOT NULL,
    matriculado_por INT NULL,
    matriculado_en  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_curso_estudiante (curso_id, estudiante_id),

    CONSTRAINT fk_mat_curso
        FOREIGN KEY (curso_id)
        REFERENCES cursos(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_mat_estudiante
        FOREIGN KEY (estudiante_id)
        REFERENCES estudiantes(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_mat_por
        FOREIGN KEY (matriculado_por)
        REFERENCES usuarios(id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------- EVALUACIONES ----------
CREATE TABLE evaluaciones (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    curso_id          INT NOT NULL,
    nombre            VARCHAR(150) NOT NULL,
    fecha_vencimiento DATE NULL,
    peso              DECIMAL(5,2) NOT NULL DEFAULT 0,
    creado_por        INT NULL,
    creado_en         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_eval_curso
        FOREIGN KEY (curso_id)
        REFERENCES cursos(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_eval_por
        FOREIGN KEY (creado_por)
        REFERENCES usuarios(id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------- NOTAS ----------
CREATE TABLE notas (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    evaluacion_id  INT NOT NULL,
    estudiante_id  INT NOT NULL,
    nota           DECIMAL(4,2) NULL,
    estado         ENUM('pendiente','entregado','calificado') NOT NULL DEFAULT 'pendiente',
    registrada_por INT NULL,
    registrada_en  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_eval_estudiante (evaluacion_id, estudiante_id),

    CONSTRAINT chk_nota_rango
        CHECK (nota IS NULL OR (nota >= 0 AND nota <= 20)),

    CONSTRAINT fk_notas_eval
        FOREIGN KEY (evaluacion_id)
        REFERENCES evaluaciones(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_notas_est
        FOREIGN KEY (estudiante_id)
        REFERENCES estudiantes(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_notas_por
        FOREIGN KEY (registrada_por)
        REFERENCES usuarios(id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

-- ---------- ROSTROS ----------
-- Solo se almacenan embeddings cifrados.
-- Nunca se almacenan imágenes faciales.
CREATE TABLE rostros (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id            INT NOT NULL UNIQUE,
    embedding             BLOB NOT NULL,
    consentimiento       TINYINT(1) NOT NULL DEFAULT 0,
    fecha_consentimiento DATETIME NULL,
    login_facial_activo  TINYINT(1) NOT NULL DEFAULT 1,
    retener_hasta         DATE NULL,
    registrado_en         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_rostros_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------- SESIONES DE CLASE ----------
CREATE TABLE sesiones_clase (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    curso_id           INT NOT NULL,
    fecha              DATE NOT NULL,
    hora_inicio        TIME NOT NULL,
    hora_fin           TIME NOT NULL,
    tolerancia_minutos INT NOT NULL DEFAULT 10,
    estado             ENUM('ACTIVA','CERRADA','CANCELADA') NOT NULL DEFAULT 'ACTIVA',
    fecha_registro     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sesion_curso
        FOREIGN KEY (curso_id)
        REFERENCES cursos(id)
        ON DELETE CASCADE,

    INDEX idx_sesiones_fecha (fecha),
    INDEX idx_sesiones_curso (curso_id),
    INDEX idx_sesiones_estado (estado)
) ENGINE=InnoDB;

-- ---------- ASISTENCIAS ----------
CREATE TABLE asistencias (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id      INT NOT NULL,
    sesion_id       INT NOT NULL,
    fecha           DATE NOT NULL,
    hora            TIME NOT NULL,
    confianza       DECIMAL(10,6) NOT NULL,
    liveness_score  DECIMAL(10,6) NOT NULL,
    estado          ENUM('PRESENTE','TARDANZA','AUSENTE') NOT NULL DEFAULT 'PRESENTE',
    fecha_registro  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_asistencia_sesion_usuario (sesion_id, usuario_id),

    INDEX idx_asistencias_usuario (usuario_id),
    INDEX idx_asistencias_sesion (sesion_id),
    INDEX idx_asistencias_fecha (fecha),
    INDEX idx_asistencias_estado (estado),

    CONSTRAINT fk_asistencias_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_asistencias_sesion
        FOREIGN KEY (sesion_id)
        REFERENCES sesiones_clase(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------- AUDITORIA ----------
CREATE TABLE auditoria (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NULL,
    accion     VARCHAR(60) NOT NULL,
    detalle    VARCHAR(500) NULL,
    ip         VARCHAR(45) NULL,
    exito      TINYINT(1) NOT NULL DEFAULT 1,
    fecha      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON DELETE SET NULL
) ENGINE=InnoDB;
