-- Migración aditiva del chatbot. No borra datos ni modifica tablas existentes.
SET NAMES utf8mb4;


CREATE TABLE IF NOT EXISTS predicciones (
	id_prediccion INTEGER NOT NULL AUTO_INCREMENT, 
	id_estudiante INTEGER NOT NULL, 
	prob_falta FLOAT, 
	prob_tardanza FLOAT, 
	fecha DATE NOT NULL, 
	modelo_version VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id_prediccion), 
	FOREIGN KEY(id_estudiante) REFERENCES estudiantes (id)
)

;


CREATE TABLE IF NOT EXISTS metricas_modelo (
	id_metrica INTEGER NOT NULL AUTO_INCREMENT, 
	modelo VARCHAR(100), 
	version VARCHAR(100), 
	accuracy FLOAT, 
	`precision` FLOAT, 
	recall FLOAT, 
	f1 FLOAT, 
	PRIMARY KEY (id_metrica)
)

;


CREATE TABLE IF NOT EXISTS chat_historial (
	id_mensaje INTEGER NOT NULL AUTO_INCREMENT, 
	id_usuario INTEGER NOT NULL, 
	pregunta TEXT NOT NULL, 
	respuesta TEXT NOT NULL, 
	fecha_hora DATETIME NOT NULL, 
	PRIMARY KEY (id_mensaje), 
	FOREIGN KEY(id_usuario) REFERENCES usuarios (id)
)

;

