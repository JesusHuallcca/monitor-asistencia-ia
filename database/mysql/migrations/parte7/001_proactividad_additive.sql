-- PARTE 7 / FASE 5: PROPUESTA ADITIVA PARA REVISION; NO EJECUTAR AUTOMATICAMENTE.
-- Revisar en desarrollo primero. No incluye creacion de base ni escrituras en tablas previas.
-- Identificadores de usuario/curso/estudiante corresponden al esquema 01_schema.sql.
CREATE TABLE chatbot_proactive_actions (
 id VARCHAR(36) PRIMARY KEY,
 owner_id INT NOT NULL,
 recipient_id INT NOT NULL,
 kind VARCHAR(32) NOT NULL,
 course_id INT NULL,
 student_id INT NULL,
 source_id INT NULL,
 config_json MEDIUMTEXT NOT NULL,
 timezone VARCHAR(64) NOT NULL,
 frequency VARCHAR(12) NOT NULL,
 status VARCHAR(16) NOT NULL,
 next_run DATETIME NULL,
 last_run DATETIME NULL,
 last_signature VARCHAR(64) NULL,
 version INT NOT NULL DEFAULT 1,
 scope_key VARCHAR(64) NOT NULL,
 identity VARCHAR(64) NOT NULL,
 created_at DATETIME NOT NULL,
 updated_at DATETIME NOT NULL,
 UNIQUE KEY uq_proactive_identity (identity),
 KEY ix_proactive_due (status,next_run),
 KEY ix_proactive_owner (owner_id),
 CONSTRAINT fk_proactive_owner FOREIGN KEY(owner_id) REFERENCES usuarios(id),
 CONSTRAINT fk_proactive_recipient FOREIGN KEY(recipient_id) REFERENCES usuarios(id),
 CONSTRAINT fk_proactive_course FOREIGN KEY(course_id) REFERENCES cursos(id),
 CONSTRAINT fk_proactive_student FOREIGN KEY(student_id) REFERENCES estudiantes(id),
 CONSTRAINT ck_proactive_self CHECK(owner_id=recipient_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE chatbot_proactive_preferences (
 owner_id INT PRIMARY KEY,
 enabled BOOLEAN NOT NULL DEFAULT TRUE,
 timezone VARCHAR(64) NOT NULL DEFAULT 'America/Lima',
 updated_at DATETIME NOT NULL,
 CONSTRAINT fk_proactive_preferences_owner FOREIGN KEY(owner_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE chatbot_proactive_notifications (
 id VARCHAR(36) PRIMARY KEY,
 action_id VARCHAR(36) NOT NULL,
 owner_id INT NOT NULL,
 execution_key VARCHAR(64) NOT NULL,
 scheduled_for DATETIME NOT NULL,
 title VARCHAR(180) NOT NULL,
 message TEXT NOT NULL,
 data_json MEDIUMTEXT NOT NULL,
 scope_key VARCHAR(64) NOT NULL,
 state VARCHAR(16) NOT NULL DEFAULT 'unread',
 created_at DATETIME NOT NULL,
 expires_at DATETIME NOT NULL,
 UNIQUE KEY uq_proactive_execution (execution_key),
 KEY ix_proactive_notification_owner (owner_id),
 KEY ix_proactive_notification_action (action_id),
 CONSTRAINT fk_proactive_notification_action FOREIGN KEY(action_id) REFERENCES chatbot_proactive_actions(id),
 CONSTRAINT fk_proactive_notification_owner FOREIGN KEY(owner_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE chatbot_proactive_audit (
 id INT AUTO_INCREMENT PRIMARY KEY,
 owner_id INT NOT NULL,
 action_id VARCHAR(36) NULL,
 event VARCHAR(40) NOT NULL,
 created_at DATETIME NOT NULL,
 KEY ix_proactive_audit_owner (owner_id),
 CONSTRAINT fk_proactive_audit_owner FOREIGN KEY(owner_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE chatbot_proactive_worker (
 id VARCHAR(16) PRIMARY KEY,
 last_seen DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
