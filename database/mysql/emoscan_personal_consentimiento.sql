-- Aplicar explícitamente SOLO en una BD de desarrollo, después de revisión.
-- No guarda fotografías, videos ni puntuaciones. No se aplica automáticamente.
CREATE TABLE IF NOT EXISTS consentimientos_emoscan_personal (
  usuario_id INT NOT NULL PRIMARY KEY,
  aceptado BOOLEAN NOT NULL DEFAULT FALSE,
  texto_version VARCHAR(80) NOT NULL,
  revision VARCHAR(32) NOT NULL,
  actualizado_en DATETIME NOT NULL,
  CONSTRAINT fk_emoscan_personal_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
