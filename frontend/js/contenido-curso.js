// Pestaña "Contenido" estilo Blackboard (estudiante y profesor).
const ContenidoCurso = (() => {
  const SEMANAS = 16;

  const ESTADOS = {
    pendiente: "Pendiente",
    entregado: "Entregado",
    calificado: "Calificado",
  };

  // ===== DATOS ESTÁTICOS DE EJEMPLO (editables) =====
  const PLANES = {
    "PRG-101": {
      resumen:
        "Aprende a pensar como programador: variables, decisiones, bucles y funciones con Python.",
      aprenderas: [
        "Escribir programas en Python desde cero",
        "Resolver problemas con condicionales y bucles",
        "Organizar el código en funciones y módulos",
        "Depurar errores con método",
      ],
      unidades: [
        [
          "Introducción y entorno",
          "Instalación de Python, primer programa, variables y tipos de datos.",
        ],
        [
          "Control de flujo",
          "Condicionales, operadores lógicos y bucles for y while.",
        ],
        [
          "Funciones y módulos",
          "Parámetros, valores de retorno, alcance y uso de módulos.",
        ],
        [
          "Estructuras de datos",
          "Listas, tuplas, diccionarios y sus recorridos.",
        ],
      ],
    },

    "WEB-101": {
      resumen:
        "Construye páginas web modernas y adaptables a cualquier pantalla con HTML y CSS.",
      aprenderas: [
        "Estructurar contenido con HTML semántico",
        "Dar estilo con CSS: colores, tipografía y capas",
        "Maquetar con Flexbox y Grid",
        "Crear diseños responsive",
      ],
      unidades: [
        [
          "Fundamentos de HTML",
          "Etiquetas, enlaces, imágenes, listas y formularios.",
        ],
        [
          "Estilos con CSS",
          "Selectores, modelo de caja, colores y tipografía.",
        ],
        [
          "Maquetación",
          "Flexbox, Grid y posicionamiento.",
        ],
        [
          "Diseño responsive",
          "Media queries y proyecto final de página personal.",
        ],
      ],
    },

    "WEB-201": {
      resumen:
        "Da vida a tus páginas: lógica, eventos y manipulación del DOM con JavaScript.",
      aprenderas: [
        "Programar la lógica del navegador",
        "Responder a eventos del usuario",
        "Manipular el DOM",
        "Consumir datos de una API con fetch",
      ],
      unidades: [
        [
          "Lenguaje base",
          "Variables, funciones, arreglos y objetos.",
        ],
        [
          "El DOM y los eventos",
          "Seleccionar elementos, crear contenido y reaccionar a clics.",
        ],
        [
          "Formularios y validación",
          "Validar los datos antes de enviarlos.",
        ],
        [
          "Datos externos",
          "Peticiones con fetch y manejo de errores.",
        ],
      ],
    },

    "BD-101": {
      resumen:
        "Diseña bases de datos relacionales y consúltalas con SQL.",
      aprenderas: [
        "Modelar datos con entidad-relación",
        "Crear tablas con llaves y restricciones",
        "Consultar con SELECT, JOIN y filtros",
        "Proteger las consultas contra inyección SQL",
      ],
      unidades: [
        [
          "Modelo relacional",
          "Entidades, relaciones y normalización.",
        ],
        [
          "Creación de tablas",
          "DDL, tipos de datos y llaves.",
        ],
        [
          "Consultas SQL",
          "SELECT, filtros, JOIN y agrupaciones.",
        ],
        [
          "Buenas prácticas",
          "Índices, consultas parametrizadas y respaldos.",
        ],
      ],
    },

    "POO-201": {
      resumen:
        "Modela problemas reales con clases, objetos, herencia y polimorfismo.",
      aprenderas: [
        "Diseñar clases y objetos",
        "Aplicar encapsulamiento y herencia",
        "Usar polimorfismo",
        "Escribir código reutilizable",
      ],
      unidades: [
        [
          "Clases y objetos",
          "Atributos, métodos y constructores.",
        ],
        [
          "Encapsulamiento",
          "Visibilidad y propiedades.",
        ],
        [
          "Herencia y polimorfismo",
          "Jerarquías de clases y sobrescritura de métodos.",
        ],
        [
          "Diseño",
          "Relaciones entre clases y mini proyecto.",
        ],
      ],
    },

    "WEB-301": {
      resumen:
        "Crea APIs REST seguras con FastAPI y conéctalas a una base de datos.",
      aprenderas: [
        "Diseñar endpoints REST",
        "Validar datos con Pydantic",
        "Autenticar con JWT y controlar roles",
        "Conectar con MySQL mediante SQLAlchemy",
      ],
      unidades: [
        [
          "Fundamentos de APIs",
          "HTTP, REST y primer servidor con FastAPI.",
        ],
        [
          "Validación y modelos",
          "Pydantic y respuestas tipadas.",
        ],
        [
          "Base de datos",
          "SQLAlchemy, sesiones y consultas.",
        ],
        [
          "Seguridad",
          "Contraseñas con hash, JWT y roles.",
        ],
      ],
    },

    "GIT-101": {
      resumen:
        "Trabaja en equipo sin perder código: commits, ramas y GitHub.",
      aprenderas: [
        "Registrar cambios con commits claros",
        "Trabajar con ramas y fusionarlas",
        "Resolver conflictos",
        "Colaborar con GitHub y Pull Requests",
      ],
      unidades: [
        [
          "Primeros pasos",
          "Repositorio, add, commit y log.",
        ],
        [
          "Ramas",
          "Crear, cambiar y fusionar ramas.",
        ],
        [
          "GitHub",
          "Remotos, push, pull y clonado.",
        ],
        [
          "Trabajo en equipo",
          "Pull Requests, revisión y resolución de conflictos.",
        ],
      ],
    },

    "ALG-201": {
      resumen:
        "Organiza datos y resuelve problemas de forma eficiente.",
      aprenderas: [
        "Usar listas, pilas y colas",
        "Recorrer árboles",
        "Comparar algoritmos con su complejidad",
        "Aplicar búsqueda y ordenamiento",
      ],
      unidades: [
        [
          "Estructuras lineales",
          "Listas, pilas y colas.",
        ],
        [
          "Árboles",
          "Árboles binarios y recorridos.",
        ],
        [
          "Búsqueda y ordenamiento",
          "Algoritmos clásicos y su comparación.",
        ],
        [
          "Complejidad",
          "Notación Big O y análisis de algoritmos.",
        ],
      ],
    },

    "IA-101": {
      resumen:
        "Conoce los fundamentos del aprendizaje automático y sus aplicaciones.",
      aprenderas: [
        "Distinguir los tipos de aprendizaje automático",
        "Preparar datos para entrenar un modelo",
        "Medir un modelo con métricas",
        "Reconocer usos y límites de la IA",
      ],
      unidades: [
        [
          "Conceptos básicos",
          "Qué es la IA y el aprendizaje automático.",
        ],
        [
          "Datos",
          "Limpieza y preparación.",
        ],
        [
          "Modelos",
          "Regresión y clasificación.",
        ],
        [
          "Evaluación",
          "Métricas y buenas prácticas.",
        ],
      ],
    },
  };

  const GENERICO = {
    resumen: "Curso del programa de formación de SENATI.",
    aprenderas: [
      "Comprender los conceptos principales del curso",
      "Aplicarlos en ejercicios prácticos",
      "Trabajar en equipo en proyectos",
      "Evaluar tu propio avance",
    ],
    unidades: [
      [
        "Unidad 1",
        "Introducción a los conceptos del curso.",
      ],
      [
        "Unidad 2",
        "Desarrollo de habilidades.",
      ],
      [
        "Unidad 3",
        "Práctica guiada.",
      ],
      [
        "Unidad 4",
        "Proyecto final.",
      ],
    ],
  };

  // ---------- Utilidades ----------
  function diasHasta(iso) {
    const [y, m, d] = iso.split("-").map(Number);

    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);

    return Math.round(
      (new Date(y, m - 1, d) - hoy) / 86400000,
    );
  }

  function textoPlazo(iso) {
    if (!iso) return "Sin fecha";

    const n = diasHasta(iso);

    if (n < 0) {
      return (
        "Vencida hace " +
        -n +
        (n === -1 ? " día" : " días")
      );
    }

    if (n === 0) return "Vence hoy";

    if (n === 1) return "Vence mañana";

    return "Vence en " + n + " días";
  }

  // ---------- Vista ----------
  // o = {
  //   rol,
  //   curso,
  //   docentes,
  //   filas (estudiante)
  //   | libro (profesor)
  // }
  function pintar(o) {
    const el = Panel.el.bind(Panel);

    const tarjeta = (titulo) => {
      const s = el("section", "panel-card");

      s.appendChild(
        el("h3", "", titulo),
      );

      return s;
    };

    const { curso, docentes } = o;

    const esProfe = o.rol === "profesor";

    const raiz = document.getElementById(
      "contenido-curso",
    );

    raiz.replaceChildren();

    const plan =
      PLANES[curso.codigo] || GENERICO;

    const [c1, c2] =
      Panel.colores(curso.codigo);

    // --- Portada ---
    const hero = el(
      "div",
      "hero-curso",
    );

    hero.style.setProperty(
      "--c1",
      c1,
    );

    hero.style.setProperty(
      "--c2",
      c2,
    );

    hero.dataset.sigla =
      curso.codigo.split("-")[0];

    hero.appendChild(
      el(
        "span",
        "hero-codigo",
        curso.codigo,
      ),
    );

    hero.appendChild(
      el(
        "h2",
        "",
        curso.nombre,
      ),
    );

    hero.appendChild(
      el(
        "p",
        "",
        plan.resumen,
      ),
    );

    const chips = el(
      "div",
      "hero-chips",
    );

    const nombres = docentes.length
      ? docentes
          .map(
            (d) =>
              d.nombres +
              " " +
              d.apellidos,
          )
          .join(", ")
      : "Sin docente asignado";

    [
      "Docente: " + nombres,
      "Periodo " + curso.periodo,
      "Presencial",
      SEMANAS + " semanas",
    ].forEach((t) =>
      chips.appendChild(
        el(
          "span",
          "hero-chip",
          t,
        ),
      ),
    );

    hero.appendChild(chips);

    raiz.appendChild(hero);

    // --- Columnas ---
    const grid = el(
      "div",
      "contenido-grid",
    );

    const izq = el("div");
    const der = el("div");

    const descripcion = tarjeta(
      "Descripción del curso",
    );

    descripcion.appendChild(
      el(
        "p",
        "",
        curso.descripcion ||
          plan.resumen,
      ),
    );

    izq.appendChild(descripcion);

    const aprenderas = tarjeta(
      "Lo que aprenderás",
    );

    const checks = el(
      "ul",
      "check-lista",
    );

    plan.aprenderas.forEach((t) =>
      checks.appendChild(
        el("li", "", t),
      ),
    );

    aprenderas.appendChild(checks);

    izq.appendChild(aprenderas);

    const unidades = tarjeta(
      "Unidades del curso",
    );

    const ol = el(
      "ol",
      "unidades",
    );

    const por =
      SEMANAS /
      plan.unidades.length;

    plan.unidades.forEach(
      ([titulo, texto], i) => {
        const li = el(
          "li",
          "unidad",
        );

        li.appendChild(
          el(
            "span",
            "num-unidad",
            String(i + 1),
          ),
        );

        const cuerpo = el("div");

        cuerpo.appendChild(
          el(
            "strong",
            "",
            titulo,
          ),
        );

        cuerpo.appendChild(
          el(
            "small",
            "",
            "Semanas " +
              Math.round(
                i * por + 1,
              ) +
              " a " +
              Math.round(
                (i + 1) * por,
              ),
          ),
        );

        cuerpo.appendChild(
          el(
            "p",
            "",
            texto,
          ),
        );

        li.appendChild(cuerpo);

        ol.appendChild(li);
      },
    );

    unidades.appendChild(ol);

    izq.appendChild(unidades);

    // --- Lado derecho: información, docentes, asistencia y tareas ---
    const info = tarjeta(
      "Información del curso",
    );

    const dl = el(
      "dl",
      "datos",
    );

    const dato = (k, v) => {
      dl.appendChild(
        el("dt", "", k),
      );

      dl.appendChild(
        el("dd", "", v),
      );
    };

    dato(
      "Código",
      curso.codigo,
    );

    dato(
      "Periodo",
      curso.periodo,
    );

    dato(
      "Modalidad",
      "Presencial",
    );

    dato(
      "Duración",
      SEMANAS + " semanas",
    );

    dato(
      "Estado",
      curso.activo
        ? "Activo"
        : "Inactivo",
    );

    if (esProfe) {
      dato(
        "Estudiantes matriculados",
        String(
          o.libro.alumnos.length,
        ),
      );
    }

    info.appendChild(dl);

    der.appendChild(info);

    // --- Docente ---
    const doc = tarjeta(
      docentes.length === 1
        ? "Docente"
        : "Docentes",
    );

    const ulDoc = el(
      "ul",
      "actividad",
    );

    Panel.pintarPersonas(
      ulDoc,
      docentes,
      "Aún no hay docentes asignados.",
    );

    doc.appendChild(ulDoc);

    der.appendChild(doc);

    // --- Asistencia ---
    const asistencia = tarjeta(
      "Asistencia",
    );

    const asistenciaContenido = el(
      "div",
      "asistencia-curso",
    );

    const tituloSesion = el(
      "strong",
      "",
      "Sesión actual",
    );

    const textoSesion = el(
      "p",
      "",
      "Consultando sesión...",
    );

    const estadoSesion = el(
      "span",
      "estado asistencia-inactiva",
      "Consultando...",
    );

    asistenciaContenido.appendChild(
      tituloSesion,
    );

    asistenciaContenido.appendChild(
      textoSesion,
    );

    asistenciaContenido.appendChild(
      estadoSesion,
    );

    async function cargarSesionAsistencia() {
      try {
        const respuesta =
          await Auth.fetchAutenticado(
            `/api/attendance/session/${curso.id}`,
          );

        if (respuesta.status === 401) {
          Auth.limpiar();
          window.location.href =
            "../login.html";
          return;
        }

        if (!respuesta.ok) {
          throw new Error(
            "No se pudo consultar la sesión",
          );
        }

        const datos =
          await respuesta.json();

        if (!datos.sesion) {
          textoSesion.textContent =
            "No hay una sesión programada para hoy.";

          estadoSesion.textContent =
            "Sin sesión hoy";

          estadoSesion.className =
            "estado asistencia-inactiva";

          return;
        }

        const sesion = datos.sesion;

        const partesFecha =
          sesion.fecha.split("-");

        const fechaFormateada =
          `${partesFecha[2]}/${partesFecha[1]}/${partesFecha[0]}`;

        textoSesion.textContent =
          `${fechaFormateada} · ${sesion.hora_inicio} - ${sesion.hora_fin}`;

        if (datos.activa) {
          estadoSesion.textContent =
            "Sesión activa";

          estadoSesion.className =
            "estado asistencia-activa";

          const btnAsistencia = el(
            "button",
            "btn-secundario",
            "Registrar asistencia",
          );

          btnAsistencia.type = "button";

          btnAsistencia.addEventListener(
            "click",
            () => {
              window.location.href =
                "asistencia.html";
            },
          );

          asistenciaContenido.appendChild(
            btnAsistencia,
          );

          return;
        }

        const ahora = new Date();

        const inicio = new Date(
          `${sesion.fecha}T${sesion.hora_inicio}:00`,
        );

        const fin = new Date(
          `${sesion.fecha}T${sesion.hora_fin}:00`,
        );

        if (ahora < inicio) {
          estadoSesion.textContent =
            "Sesión programada";

          estadoSesion.className =
            "estado asistencia-inactiva";
        } else if (ahora >= fin) {
          estadoSesion.textContent =
            "Sesión finalizada";

          estadoSesion.className =
            "estado asistencia-inactiva";
        } else {
          estadoSesion.textContent =
            "Sesión no disponible";

          estadoSesion.className =
            "estado asistencia-inactiva";
        }
      } catch (error) {
        console.error(
          "Error al consultar la sesión de asistencia:",
          error,
        );

        textoSesion.textContent =
          "No se pudo consultar la sesión.";

        estadoSesion.textContent =
          "No disponible";

        estadoSesion.className =
          "estado asistencia-inactiva";
      }
    }

    asistencia.appendChild(
      asistenciaContenido,
    );

    der.appendChild(asistencia);

    cargarSesionAsistencia();

    // --- Tareas ---
    const tareas = tarjeta(
      esProfe
        ? "Evaluaciones del curso"
        : "Tareas por realizar",
    );

    const ulT = el(
      "ul",
      "actividad",
    );

    if (esProfe) {
      const total =
        o.libro.alumnos.length;

      if (
        o.libro.evaluaciones.length ===
        0
      ) {
        ulT.appendChild(
          el(
            "li",
            "vacio-lista",
            "Aún no creaste evaluaciones.",
          ),
        );
      }

      for (const e of o.libro
        .evaluaciones) {
        const calificadas =
          o.libro.alumnos.filter(
            (a) =>
              a.notas.some(
                (n) =>
                  n.evaluacion_id ===
                    e.id &&
                  n.estado ===
                    "calificado",
              ),
          ).length;

        const li = el("li");

        const textos = el(
          "div",
        );

        textos.appendChild(
          el(
            "strong",
            "",
            e.nombre,
          ),
        );

        textos.appendChild(
          document.createElement(
            "br",
          ),
        );

        textos.appendChild(
          el(
            "small",
            "",
            Panel.fechaDia(
              e.fecha_vencimiento,
            ) +
              " · Peso " +
              e.peso +
              "%",
          ),
        );

        li.appendChild(textos);

        li.appendChild(
          el(
            "span",
            "estado " +
              (total > 0 &&
              calificadas === total
                ? "calificado"
                : "pendiente"),
            calificadas +
              " de " +
              total,
          ),
        );

        ulT.appendChild(li);
      }
    } else {
      const pendientes = o.filas
        .filter(
          (f) =>
            f.estado !==
            "calificado",
        )
        .sort((a, b) =>
          (
            a.fecha_vencimiento ||
            "9999"
          ).localeCompare(
            b.fecha_vencimiento ||
              "9999",
          ),
        );

      if (
        pendientes.length === 0
      ) {
        ulT.appendChild(
          el(
            "li",
            "vacio-lista",
            o.filas.length
              ? "¡Estás al día! No tienes tareas pendientes."
              : "Tu docente aún no publicó tareas.",
          ),
        );
      }

      for (const f of pendientes.slice(
        0,
        5,
      )) {
        const vencida =
          f.fecha_vencimiento &&
          diasHasta(
            f.fecha_vencimiento,
          ) < 0 &&
          f.estado ===
            "pendiente";

        const li = el("li");

        const textos = el(
          "div",
        );

        textos.appendChild(
          el(
            "strong",
            "",
            f.nombre,
          ),
        );

        textos.appendChild(
          document.createElement(
            "br",
          ),
        );

        textos.appendChild(
          el(
            "small",
            "",
            textoPlazo(
              f.fecha_vencimiento,
            ) +
              " · Peso " +
              f.peso +
              "%",
          ),
        );

        li.appendChild(textos);

        li.appendChild(
          el(
            "span",
            "estado " +
              (vencida
                ? "fallo"
                : f.estado),
            vencida
              ? "Vencida"
              : ESTADOS[f.estado],
          ),
        );

        ulT.appendChild(li);
      }
    }

    tareas.appendChild(ulT);

    // --- Ir al libro de calificaciones ---
    const ir = el(
      "button",
      "btn-secundario",
      "Ir al libro de calificaciones",
    );

    ir.type = "button";

    ir.style.marginTop = "12px";

    ir.addEventListener(
      "click",
      () =>
        document
          .querySelector(
            '.pestana[data-tab="notas"]',
          )
          .click(),
    );

    tareas.appendChild(ir);

    der.appendChild(tareas);

    grid.appendChild(izq);
    grid.appendChild(der);

    raiz.appendChild(grid);
  }

  return {
    pintar,
  };
})();