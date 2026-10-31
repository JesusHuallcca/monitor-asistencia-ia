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
('admin1',       'admin1@example.com',       @hash, 'Lucía',   'Paredes',   'admin',      'activo'),
('prof.ramirez', 'prof.ramirez@example.com', @hash, 'Carlos',  'Ramírez',   'profesor',   'activo'),
('prof.torres',  'prof.torres@example.com',  @hash, 'Marta',   'Torres',    'profesor',   'activo'),
('prof.nuevo',   'prof.nuevo@example.com',   @hash, 'Jorge',   'Salas',     'profesor',   'pendiente'),
('alumno1',      'alumno1@example.com',      @hash, 'Ana',     'Quispe',    'estudiante', 'activo'),
('alumno2',      'alumno2@example.com',      @hash, 'Luis',    'Mendoza',   'estudiante', 'activo'),
('alumno3',      'alumno3@example.com',      @hash, 'Sofía',   'Huamán',    'estudiante', 'activo'),
('alumno4',      'alumno4@example.com',      @hash, 'Diego',   'Vargas',    'estudiante', 'activo'),
('alumno5',      'alumno5@example.com',      @hash, 'Valeria', 'Rojas',     'estudiante', 'activo');

-- ---------- Profesores ----------
INSERT INTO profesores (usuario_id, especialidad)
SELECT id,
       CASE username
            WHEN 'prof.ramirez' THEN 'Programación y algoritmos'
            WHEN 'prof.torres'  THEN 'Desarrollo web y bases de datos'
            ELSE 'Redes y sistemas'
       END
FROM usuarios WHERE rol = 'profesor';

-- ---------- Estudiantes ----------
INSERT INTO estudiantes (usuario_id, codigo, carrera, ciclo)
SELECT id,
       CONCAT('EST-', LPAD(id, 4, '0')),
       'Ingeniería de Software con IA',
       '2026-I'
FROM usuarios WHERE rol = 'estudiante';

-- ---------- Cursos ----------
INSERT INTO cursos (codigo, nombre, descripcion) VALUES
('PRG-101', 'Fundamentos de Programación con Python', 'Variables, control de flujo, funciones y estructuras básicas'),
('WEB-101', 'HTML y CSS',                             'Estructura web semántica, CSS Grid y Flexbox'),
('WEB-201', 'JavaScript',                            'DOM, asincronía con promesas/async, consumo de APIs'),
('BD-101',  'Bases de Datos con MySQL',               'Modelado relacional, DDL, DML y consultas complejas'),
('POO-201', 'Programación Orientada a Objetos',       'Clases, herencia, polimorfismo y patrones básicos'),
('WEB-301', 'Desarrollo Backend con FastAPI',         'APIs REST, inyección de dependencias y OpenAPI'),
('GIT-101', 'Control de Versiones con Git',          'Ramas, merge, rebase y flujos colaborativos'),
('ALG-201', 'Estructuras de Datos y Algoritmos',      'Listas, pilas, colas, árboles y complejidad temporal');

-- ---------- Asignaciones Profesor -> Curso ----------
INSERT INTO asignaciones_profesor (profesor_id, curso_id)
SELECT p.id, c.id
FROM profesores p
JOIN usuarios u ON u.id = p.usuario_id
JOIN cursos c ON (
    (u.username = 'prof.ramirez' AND c.codigo IN ('PRG-101', 'POO-201', 'ALG-201')) OR
    (u.username = 'prof.torres'  AND c.codigo IN ('WEB-101', 'WEB-201', 'BD-101', 'WEB-301', 'GIT-101'))
);

-- ---------- Matriculas Estudiante -> Curso ----------
INSERT INTO matriculas (estudiante_id, curso_id)
SELECT e.id, c.id
FROM estudiantes e
JOIN usuarios u ON u.id = e.usuario_id
JOIN cursos c ON (
    (u.username = 'alumno1' AND c.codigo IN ('PRG-101', 'WEB-101', 'WEB-201', 'BD-101')) OR
    (u.username = 'alumno2' AND c.codigo IN ('PRG-101', 'WEB-101', 'POO-201', 'GIT-101')) OR
    (u.username = 'alumno3' AND c.codigo IN ('PRG-101', 'BD-101',  'WEB-301', 'ALG-201')) OR
    (u.username = 'alumno4' AND c.codigo IN ('WEB-101', 'WEB-201', 'BD-101',  'ALG-201')) OR
    (u.username = 'alumno5' AND c.codigo IN ('PRG-101', 'WEB-201', 'POO-201', 'GIT-101'))
);

-- =====================================================
-- Sesiones de clase a gran escala (Semestre 2026)
-- =====================================================
INSERT INTO sesiones_clase (curso_id, fecha, hora_inicio, hora_fin, tolerancia_minutos, estado)
SELECT c.id, f.fecha, '08:00:00', '12:00:00', 15,
       CASE WHEN f.fecha = '2026-10-29' THEN 'ACTIVA' ELSE 'CERRADA' END
FROM cursos c
CROSS JOIN (
    SELECT '2026-08-17' AS fecha UNION ALL
    SELECT '2026-08-24' UNION ALL
    SELECT '2026-08-31' UNION ALL
    SELECT '2026-09-07' UNION ALL
    SELECT '2026-09-14' UNION ALL
    SELECT '2026-09-21' UNION ALL
    SELECT '2026-09-28' UNION ALL
    SELECT '2026-10-05' UNION ALL
    SELECT '2026-10-12' UNION ALL
    SELECT '2026-10-19' UNION ALL
    SELECT '2026-10-26' UNION ALL
    SELECT '2026-10-29'
) f;

-- ---------- Evaluaciones ----------
INSERT INTO evaluaciones (curso_id, nombre, fecha_vencimiento, peso)
SELECT c.id, m.nombre, m.fecha, m.peso
FROM (
    SELECT 'PRG-101' AS codigo, 'Tarea 1: Variables y tipos' AS nombre, '2026-10-10' AS fecha, 20 AS peso UNION ALL
    SELECT 'PRG-101', 'Práctica calificada 1',                '2026-10-24', 30 UNION ALL
    SELECT 'PRG-101', 'Examen parcial',                       '2026-11-14', 50 UNION ALL
    SELECT 'WEB-101', 'Proyecto: página personal',            '2026-10-15', 40 UNION ALL
    SELECT 'WEB-101', 'Examen de HTML y CSS',                 '2026-11-05', 60 UNION ALL
    SELECT 'BD-101',  'Diseño del modelo entidad-relación',   '2026-10-20', 40 UNION ALL
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

-- =====================================================
-- Asistencias Biométricas Masivas (200+ registros)
-- =====================================================
INSERT INTO asistencias (
    usuario_id,
    sesion_id,
    fecha,
    hora,
    confianza,
    liveness_score,
    estado,
    fecha_registro
)
SELECT 
    e.usuario_id,
    s.id AS sesion_id,
    s.fecha,
    CASE 
        WHEN (e.id * 7 + s.id * 13 + DAY(s.fecha)) % 10 IN (0, 1) THEN '08:12:30'
        WHEN (e.id * 7 + s.id * 13 + DAY(s.fecha)) % 20 = 0 THEN '08:00:00'
        ELSE ADDTIME('08:01:00', SEC_TO_TIME(((e.id * 11 + s.id * 17) % 360)))
    END AS hora,
    ROUND(0.960000 + (((e.id * 7 + s.id * 13) % 35) / 1000.0), 6) AS confianza,
    ROUND(0.970000 + (((e.id * 5 + s.id * 11) % 28) / 1000.0), 6) AS liveness_score,
    CASE 
        WHEN s.estado = 'ACTIVA' AND (e.id % 2 = 0) THEN 'PRESENTE'
        WHEN s.estado = 'ACTIVA' THEN 'PRESENTE'
        WHEN (e.id * 7 + s.id * 13 + DAY(s.fecha)) % 20 = 0 THEN 'AUSENTE'
        WHEN (e.id * 7 + s.id * 13 + DAY(s.fecha)) % 10 IN (0, 1) THEN 'TARDANZA'
        ELSE 'PRESENTE'
    END AS estado,
    TIMESTAMP(s.fecha, '08:02:00') AS fecha_registro
FROM sesiones_clase s
JOIN matriculas m ON m.curso_id = s.curso_id
JOIN estudiantes e ON e.id = m.estudiante_id
ON DUPLICATE KEY UPDATE estado = VALUES(estado);
