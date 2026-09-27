CREATE DATABASE IF NOT EXISTS monitor_asistencia
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE monitor_asistencia;

CREATE TABLE IF NOT EXISTS rostros (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    person_id VARCHAR(100) NOT NULL,
    embedding JSON NOT NULL,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    UNIQUE KEY uk_rostros_person_id (person_id)
);

CREATE TABLE IF NOT EXISTS asistencias (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    person_id VARCHAR(100) NOT NULL,
    fecha DATE NOT NULL,
    hora TIME NOT NULL,
    confianza DECIMAL(10, 6) NOT NULL,
    liveness_score DECIMAL(10, 6) NOT NULL,
    estado VARCHAR(30) NOT NULL DEFAULT 'PRESENTE',
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_asistencia_persona_fecha (person_id, fecha),

    INDEX idx_asistencias_person_id (person_id),
    INDEX idx_asistencias_fecha (fecha),
    INDEX idx_asistencias_estado (estado)
);
CREATE TABLE IF NOT EXISTS sesiones_clase (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    curso_id BIGINT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    tolerancia_minutos INT NOT NULL DEFAULT 10,
    estado VARCHAR(30) NOT NULL DEFAULT 'ACTIVA',
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_sesiones_fecha (fecha),
    INDEX idx_sesiones_estado (estado),
    INDEX idx_sesiones_curso (curso_id)
);