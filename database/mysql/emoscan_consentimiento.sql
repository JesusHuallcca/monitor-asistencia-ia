-- Apply explicitly once. Does not alter face/attendance/segmentation tables.
-- Only consent metadata is stored; no image or expression result columns.
CREATE TABLE IF NOT EXISTS consentimientos_expresiones (
    usuario_id INT NOT NULL PRIMARY KEY,
    aceptado BOOLEAN NOT NULL DEFAULT FALSE,
    texto_version VARCHAR(80) NOT NULL,
    revision VARCHAR(32) NOT NULL,
    actualizado_en DATETIME NOT NULL,
    CONSTRAINT fk_consentimiento_expresiones_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);
