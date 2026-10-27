-- Tabla para persistir el historial de expresiones/emociones de EmoScan por estudiante_id
-- Permite consultar la evolución emocional según estudiante_id tanto para el estudiante como para el profesor

CREATE TABLE IF NOT EXISTS emoscan_historial (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    estudiante_id INT NULL,
    emocion_predominante VARCHAR(50) NOT NULL,
    confianza DECIMAL(5, 4) NULL,
    scores_json TEXT NULL,
    origen VARCHAR(30) NOT NULL DEFAULT 'personal',
    sesion_id INT NULL,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_emoscan_historial_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    CONSTRAINT fk_emoscan_historial_estudiante
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE,
    CONSTRAINT fk_emoscan_historial_sesion
        FOREIGN KEY (sesion_id) REFERENCES sesiones_clase(id) ON DELETE SET NULL,
    INDEX idx_emoscan_estudiante_fecha (estudiante_id, fecha_registro),
    INDEX idx_emoscan_usuario_fecha (usuario_id, fecha_registro)
);
