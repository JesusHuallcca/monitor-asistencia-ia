-- =====================================================
-- 02_seed.sql - Datos de prueba (ficticios)
-- Contrasena de TODAS las cuentas de prueba: Senati2026!
-- =====================================================
SET NAMES utf8mb4;

-- Hash bcrypt de la contrasena de prueba (pegar el generado)
SET @hash = '$2b$12$8SQjbfOnE0NFPtRl5EpZD.7K4Irix7ZaKBriC3MJn7o.dlUWylGle';

-- ---------- Limpiar datos previos ----------
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE asistencias;
TRUNCATE TABLE sesiones_clase;
TRUNCATE TABLE auditoria;
TRUNCATE TABLE rostros;
TRUNCATE TABLE notas;
TRUNCATE TABLE evaluaciones;
TRUNCATE TABLE matriculas;
TRUNCATE TABLE asignaciones_profesor;
TRUNCATE TABLE cursos;
TRUNCATE TABLE estudiantes;
TRUNCATE TABLE profesores;
TRUNCATE TABLE usuarios;
SET FOREIGN_KEY_CHECKS = 1;

-- ---------- Usuarios ----------
INSERT INTO usuarios (username, email, password_hash, nombres, apellidos, rol, estado) VALUES
('superadmin',   'superadmin@example.com',   @hash, 'Admin',   'Principal', 'superadmin', 'activo'),
('admin1',       'admin1@example.com',       @hash, 'LucÃ­a',   'Paredes',   'admin',      'activo'),
('prof.ramirez', 'prof.ramirez@example.com', @hash, 'Carlos',  'RamÃ­rez',   'profesor',   'activo'),
('prof.torres',  'prof.torres@example.com',  @hash, 'Marta',   'Torres',    'profesor',   'activo'),
('prof.nuevo',   'prof.nuevo@example.com',   @hash, 'Jorge',   'Salas',     'profesor',   'pendiente'),
('alumno1',      'alumno1@example.com',      @hash, 'Ana',     'Quispe',    'estudiante', 'activo'),
('alumno2',      'alumno2@example.com',      @hash, 'Luis',    'Mendoza',   'estudiante', 'activo'),
('alumno3',      'alumno3@example.com',      @hash, 'SofÃ­a',   'HuamÃ¡n',    'estudiante', 'activo'),
('alumno4',      'alumno4@example.com',      @hash, 'Diego',   'Vargas',    'estudiante', 'activo'),
('alumno5',      'alumno5@example.com',      @hash, 'Valeria', 'Rojas',     'estudiante', 'activo');

-- ---------- Profesores ----------
INSERT INTO profesores (usuario_id, especialidad)
SELECT id,
       CASE username
            WHEN 'prof.ramirez' THEN 'ProgramaciÃ³n y algoritmos'
            WHEN 'prof.torres'  THEN 'Desarrollo web y bases de datos'
            ELSE 'Redes y sistemas'
       END
FROM usuarios WHERE rol = 'profesor';

-- ---------- Estudiantes ----------
INSERT INTO estudiantes (usuario_id, codigo, carrera, ciclo)
SELECT id, CONCAT('E2026-00', RIGHT(username, 1)), 'Desarrollo de Software', 3
FROM usuarios WHERE rol = 'estudiante';

-- ---------- Cursos (ficticios, de programaciÃ³n) ----------
INSERT INTO cursos (codigo, nombre, descripcion, periodo) VALUES
('PRG-101', 'Fundamentos de ProgramaciÃ³n con Python', 'Variables, condicionales, bucles y funciones.',            '2026-II'),
('WEB-101', 'HTML y CSS',                             'MaquetaciÃ³n de pÃ¡ginas web responsive.',                    '2026-II'),
('WEB-201', 'JavaScript',                             'LÃ³gica en el navegador, DOM y eventos.',                    '2026-II'),
('BD-101',  'Bases de Datos con MySQL',               'Modelo entidad-relaciÃ³n, SQL y consultas.',                 '2026-II'),
('POO-201', 'ProgramaciÃ³n Orientada a Objetos',       'Clases, herencia y polimorfismo.',                          '2026-II'),
('WEB-301', 'Desarrollo Backend con FastAPI',         'APIs REST, autenticaciÃ³n y conexiÃ³n a base de datos.',      '2026-II'),
('GIT-101', 'Control de Versiones con Git',           'Ramas, commits, merge y trabajo en equipo con GitHub.',     '2026-II'),
('ALG-201', 'Estructuras de Datos y Algoritmos',      'Listas, pilas, colas, Ã¡rboles y complejidad.',              '2026-II');

-- ---------- Asignacion de cursos a profesores ----------
INSERT INTO asignaciones_profesor (curso_id, profesor_id, asignado_por)
SELECT c.id, p.id, (SELECT id FROM usuarios WHERE username = 'admin1')
FROM (
    SELECT 'PRG-101' AS codigo, 'prof.ramirez' AS username UNION ALL
    SELECT 'POO-201', 'prof.ramirez' UNION ALL
    SELECT 'ALG-201', 'prof.ramirez' UNION ALL
    SELECT 'WEB-101', 'prof.torres'  UNION ALL
    SELECT 'WEB-201', 'prof.torres'  UNION ALL
    SELECT 'WEB-301', 'prof.torres'  UNION ALL
    SELECT 'BD-101',  'prof.torres'  UNION ALL
    SELECT 'GIT-101', 'prof.torres'
) m
JOIN cursos c    ON c.codigo = m.codigo
JOIN usuarios u  ON u.username = m.username
JOIN profesores p ON p.usuario_id = u.id;

-- ---------- Matriculas ----------
INSERT INTO matriculas (curso_id, estudiante_id, matriculado_por)
SELECT c.id, e.id, (SELECT id FROM usuarios WHERE username = 'admin1')
FROM (
    SELECT 'alumno1' AS username, 'PRG-101' AS codigo UNION ALL
    SELECT 'alumno1', 'WEB-101' UNION ALL
    SELECT 'alumno1', 'WEB-201' UNION ALL
    SELECT 'alumno1', 'BD-101'  UNION ALL
    SELECT 'alumno2', 'PRG-101' UNION ALL
    SELECT 'alumno2', 'WEB-101' UNION ALL
    SELECT 'alumno2', 'GIT-101' UNION ALL
    SELECT 'alumno2', 'ALG-201' UNION ALL
    SELECT 'alumno3', 'PRG-101' UNION ALL
    SELECT 'alumno3', 'WEB-201' UNION ALL
    SELECT 'alumno3', 'BD-101'  UNION ALL
    SELECT 'alumno3', 'POO-201' UNION ALL
    SELECT 'alumno4', 'WEB-101' UNION ALL
    SELECT 'alumno4', 'WEB-201' UNION ALL
    SELECT 'alumno4', 'WEB-301' UNION ALL
    SELECT 'alumno4', 'GIT-101' UNION ALL
    SELECT 'alumno5', 'PRG-101' UNION ALL
    SELECT 'alumno5', 'BD-101'  UNION ALL
    SELECT 'alumno5', 'POO-201' UNION ALL
    SELECT 'alumno5', 'ALG-201'
) m
JOIN usuarios u     ON u.username = m.username
JOIN estudiantes e  ON e.usuario_id = u.id
JOIN cursos c       ON c.codigo = m.codigo;

-- =====================================================
-- Sesiones de clase
-- =====================================================

INSERT INTO sesiones_clase (
    curso_id,
    fecha,
    hora_inicio,
    hora_fin,
    tolerancia_minutos,
    estado
)
SELECT
    id,
    '2026-10-01',
    '07:00:00',
    '22:00:00',
    10,
    'ACTIVA'
FROM cursos
WHERE codigo IN ('PRG-101', 'WEB-101', 'BD-101');

INSERT INTO sesiones_clase (
    curso_id,
    fecha,
    hora_inicio,
    hora_fin,
    tolerancia_minutos,
    estado
)
SELECT
    id,
    '2026-09-30',
    '07:00:00',
    '22:00:00',
    10,
    'CERRADA'
FROM cursos
WHERE codigo IN ('PRG-101', 'WEB-101');

-- ---------- Evaluaciones ----------
INSERT INTO evaluaciones (curso_id, nombre, fecha_vencimiento, peso)
SELECT c.id, m.nombre, m.fecha, m.peso
FROM (
    SELECT 'PRG-101' AS codigo, 'Tarea 1: Variables y tipos' AS nombre, '2026-10-10' AS fecha, 20 AS peso UNION ALL
    SELECT 'PRG-101', 'PrÃ¡ctica calificada 1',                '2026-10-24', 30 UNION ALL
    SELECT 'PRG-101', 'Examen parcial',                       '2026-11-14', 50 UNION ALL
    SELECT 'WEB-101', 'Proyecto: pÃ¡gina personal',            '2026-10-15', 40 UNION ALL
    SELECT 'WEB-101', 'Examen de HTML y CSS',                 '2026-11-05', 60 UNION ALL
    SELECT 'BD-101',  'DiseÃ±o del modelo entidad-relaciÃ³n',   '2026-10-20', 40 UNION ALL
    SELECT 'BD-101',  'Examen de consultas SQL',              '2026-11-10', 60
) m
JOIN cursos c ON c.codigo = m.codigo;

-- ---------- Notas: una fila por (evaluacion, estudiante matriculado) ----------
INSERT INTO notas (evaluacion_id, estudiante_id, estado)
SELECT ev.id, m.estudiante_id, 'pendiente'
FROM evaluaciones ev
JOIN matriculas m ON m.curso_id = ev.curso_id;

-- Notas ficticias solo para las primeras evaluaciones (rango 13 a 19)
UPDATE notas n
JOIN evaluaciones ev ON ev.id = n.evaluacion_id
SET n.nota = 13 + (n.estudiante_id MOD 7),
    n.estado = 'calificado'
WHERE ev.nombre LIKE 'Tarea 1%' OR ev.nombre LIKE 'Proyecto:%';

