// Lógica interactiva del Panel de Estudiante (Campus Virtual Asistencia IA)

document.addEventListener("DOMContentLoaded", async () => {
  // Función para normalizar y limpiar cualquier error de encoding UTF-8 / Latin1
  function limpiarTexto(str) {
    if (!str) return "";
    return str
      .replace(/Ã¡/g, "á")
      .replace(/Ã©/g, "é")
      .replace(/Ã­/g, "í")
      .replace(/Ã³/g, "ó")
      .replace(/Ãº/g, "ú")
      .replace(/Ã±/g, "ñ")
      .replace(/Ã/g, "Á")
      .replace(/Ã‰/g, "É")
      .replace(/Ã/g, "Í")
      .replace(/Ã“/g, "Ó")
      .replace(/Ãš/g, "Ú")
      .replace(/Ã‘/g, "Ñ");
  }

  // Cursos reales predeterminados basados en la base de datos (con banners temáticos)
  const BANNER_MAP = {
    "PRG-101": "../assets/img/banner_python.jpg",
    "WEB-101": "../assets/img/banner_ia.jpg",
    "WEB-201": "../assets/img/banner_cyber.jpg",
    "BD-101": "../assets/img/banner_stats.jpg",
    "POO-201": "../assets/img/banner_python.jpg",
    "WEB-301": "../assets/img/banner_cyber.jpg",
    "GIT-101": "../assets/img/banner_ia.jpg",
    "ALG-201": "../assets/img/banner_stats.jpg"
  };

  const HORARIOS_MAP = {
    "PRG-101": { dias: "Lun - Mié - Vie", horario: "14:00 - 16:00", estudiantes: 32, seccion: "Sección 01" },
    "WEB-101": { dias: "Mar - Jue", horario: "10:00 - 12:00", estudiantes: 28, seccion: "Sección 01" },
    "WEB-201": { dias: "Mar - Jue", horario: "16:00 - 18:00", estudiantes: 33, seccion: "Sección 01" },
    "BD-101": { dias: "Lun - Mié", horario: "08:00 - 16:00", estudiantes: 35, seccion: "Sección 01" }
  };

  let cursosActivos = [
    {
      id: 1,
      codigo: "PRG-101",
      nombre: "Fundamentos de Programación con Python",
      banner: "../assets/img/banner_python.jpg",
      seccion: "Sección 01",
      estudiantes: 32,
      dias: "Lun - Mié - Vie",
      horario: "14:00 - 16:00",
      nota: 14.0,
      activo: true,
      periodo: "2026-II"
    },
    {
      id: 2,
      codigo: "WEB-101",
      nombre: "HTML y CSS",
      banner: "../assets/img/banner_ia.jpg",
      seccion: "Sección 01",
      estudiantes: 28,
      dias: "Mar - Jue",
      horario: "10:00 - 12:00",
      nota: 14.0,
      activo: true,
      periodo: "2026-II"
    },
    {
      id: 3,
      codigo: "WEB-201",
      nombre: "JavaScript",
      banner: "../assets/img/banner_cyber.jpg",
      seccion: "Sección 01",
      estudiantes: 33,
      dias: "Mar - Jue",
      horario: "16:00 - 18:00",
      nota: 15.0,
      activo: true,
      periodo: "2026-II"
    },
    {
      id: 4,
      codigo: "BD-101",
      nombre: "Bases de Datos con MySQL",
      banner: "../assets/img/banner_stats.jpg",
      seccion: "Sección 01",
      estudiantes: 35,
      dias: "Lun - Mié",
      horario: "08:00 - 16:00",
      nota: 14.0,
      activo: true,
      periodo: "2026-II"
    }
  ];

  // Elementos DOM
  const studentNameEl = document.getElementById("student-name");
  const studentRoleEl = document.getElementById("student-role");
  const statCursosEl = document.getElementById("stat-cursos-count");
  const statPromedioEl = document.getElementById("stat-promedio-val");
  const statTareasEl = document.getElementById("stat-tareas-count");
  const statAsistenciasEl = document.getElementById("stat-asistencias-val");
  const coursesGridEl = document.getElementById("courses-grid");
  const inputSearchCourse = document.getElementById("input-search-course");
  const inputGlobalSearch = document.getElementById("input-global-search");
  const selectPeriodo = document.getElementById("select-periodo");
  const btnHamburger = document.getElementById("btn-hamburger");
  const sidebarEl = document.getElementById("dashboard-sidebar");
  const btnLogout = document.getElementById("btn-logout");
  const btnNotify = document.getElementById("btn-notify");

  // Cargar usuario autenticado si existe sesión activa
  async function cargarUsuarioSesion() {
    if (typeof Auth !== "undefined" && Auth.token()) {
      try {
        const resp = await Auth.fetchAutenticado("/api/users/me");
        if (resp && resp.ok) {
          const user = await resp.json();
          if (studentNameEl) studentNameEl.textContent = limpiarTexto(`${user.nombres} ${user.apellidos}`);
          if (studentRoleEl) studentRoleEl.textContent = user.rol === "estudiante" ? "Estudiante" : user.rol;
          
          await cargarCursosRealesAPI();
          return;
        }
      } catch (err) {
        console.warn("Modo local o sin sesión activa:", err);
      }
    }
  }

  // Cargar cursos reales asignados al estudiante desde /api/cursos
  async function cargarCursosRealesAPI() {
    try {
      const resp = await Auth.fetchAutenticado("/api/cursos");
      if (resp && resp.ok) {
        const data = await resp.json();
        if (Array.isArray(data) && data.length > 0) {
          cursosActivos = await Promise.all(data.map(async (c) => {
            const codigo = c.codigo || "CURSO";
            const infoHorario = HORARIOS_MAP[codigo] || {
              dias: "Horario regular",
              horario: "Turno mañana",
              estudiantes: 30,
              seccion: "Sección 01"
            };
            const banner = BANNER_MAP[codigo] || "../assets/img/banner_python.jpg";

            // Intentar obtener nota real del curso
            let nota = 14.0;
            try {
              const resNota = await Auth.fetchAutenticado(`/api/cursos/${c.id}/mis-notas`);
              if (resNota && resNota.ok) {
                const notasData = await resNota.json();
                if (notasData.promedio_actual !== null && notasData.promedio_actual !== undefined) {
                  nota = Number(notasData.promedio_actual);
                }
              }
            } catch (e) {
              // Mantener nota estimada
            }

            return {
              id: c.id,
              codigo: codigo,
              nombre: limpiarTexto(c.nombre),
              banner: banner,
              seccion: infoHorario.seccion,
              estudiantes: infoHorario.estudiantes,
              dias: infoHorario.dias,
              horario: infoHorario.horario,
              nota: nota,
              activo: c.activo !== false,
              periodo: c.periodo || "2026-II"
            };
          }));

          renderizarCursos();
          actualizarStats();
          actualizarGrafico();
        }
      }
    } catch (e) {
      console.warn("Usando catálogo de cursos local", e);
    }
  }

  function actualizarStats() {
    if (statCursosEl) statCursosEl.textContent = cursosActivos.length;
    
    // Promedio general de los cursos con nota
    if (statPromedioEl) {
      const notasValidas = cursosActivos.map(c => c.nota).filter(n => typeof n === "number" && !isNaN(n));
      const promedio = notasValidas.length > 0 
        ? (notasValidas.reduce((a, b) => a + b, 0) / notasValidas.length).toFixed(1)
        : "14.0";
      statPromedioEl.textContent = promedio;
    }

    if (statTareasEl) statTareasEl.textContent = "4";
    if (statAsistenciasEl) statAsistenciasEl.textContent = "100%";
  }

  function renderizarCursos(filtro = "") {
    if (!coursesGridEl) return;
    coursesGridEl.replaceChildren();

    const query = filtro.trim().toLowerCase();
    const filtrados = cursosActivos.filter(c => 
      c.nombre.toLowerCase().includes(query) || 
      c.codigo.toLowerCase().includes(query)
    );

    if (filtrados.length === 0) {
      const emptyDiv = document.createElement("div");
      emptyDiv.style.gridColumn = "1 / -1";
      emptyDiv.style.padding = "35px 20px";
      emptyDiv.style.textAlign = "center";
      emptyDiv.style.color = "#64748b";
      emptyDiv.innerHTML = `<p>No se encontraron cursos que coincidan con "<strong>${filtro}</strong>".</p>`;
      coursesGridEl.appendChild(emptyDiv);
      return;
    }

    filtrados.forEach(c => {
      const card = document.createElement("article");
      card.className = "course-card-item";

      const nombreLimpio = limpiarTexto(c.nombre);

      card.innerHTML = `
        <div class="course-banner-box">
          <img src="${c.banner}" alt="${nombreLimpio}" loading="lazy" />
          <span class="course-status-pill">${c.activo ? "Activo" : "Inactivo"}</span>
        </div>
        <div class="course-body-box">
          <div class="course-top-title-row">
            <h3 class="course-title-text">${nombreLimpio}</h3>
            <button class="course-more-btn" title="Opciones" aria-label="Opciones">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="5" r="2"/>
                <circle cx="12" cy="12" r="2"/>
                <circle cx="12" cy="19" r="2"/>
              </svg>
            </button>
          </div>
          <div class="course-code-subtitle">${c.codigo} | ${c.seccion}</div>
          
          <div class="course-info-list">
            <div class="course-info-line">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              <span>${c.estudiantes} estudiantes</span>
            </div>
            <div class="course-info-line">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
              <span>${c.dias}</span>
            </div>
            <div class="course-info-line">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              <span>${c.horario}</span>
            </div>
          </div>

          <a href="curso.html?id=${c.id}" class="course-action-button">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </svg>
            Ver curso
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </a>
        </div>
      `;

      coursesGridEl.appendChild(card);
    });
  }

  function actualizarGrafico() {
    const bars = document.querySelectorAll(".bar-col");
    cursosActivos.slice(0, 4).forEach((c, idx) => {
      if (bars[idx]) {
        const valPill = bars[idx].querySelector(".bar-pill-value");
        const fill = bars[idx].querySelector(".bar-fill");
        const label = document.querySelectorAll(".chart-x-label")[idx];
        
        const notaStr = typeof c.nota === "number" ? c.nota.toFixed(1) : "14.0";
        const porcentaje = Math.min(100, Math.round((c.nota / 20) * 100));

        if (valPill) valPill.textContent = notaStr;
        if (fill) fill.style.height = `${porcentaje}%`;
        if (label) label.textContent = limpiarTexto(c.nombre.split(" ")[0] + " " + (c.nombre.split(" ")[1] || ""));
      }
    });
  }

  // Búsqueda en vivo
  if (inputSearchCourse) {
    inputSearchCourse.addEventListener("input", (e) => {
      renderizarCursos(e.target.value);
    });
  }

  if (inputGlobalSearch) {
    inputGlobalSearch.addEventListener("input", (e) => {
      renderizarCursos(e.target.value);
    });
  }

  if (selectPeriodo) {
    selectPeriodo.addEventListener("change", (e) => {
      renderizarCursos(inputSearchCourse ? inputSearchCourse.value : "");
    });
  }

  if (btnHamburger && sidebarEl) {
    btnHamburger.addEventListener("click", () => {
      sidebarEl.classList.toggle("open");
    });
  }

  if (btnLogout) {
    btnLogout.addEventListener("click", () => {
      if (typeof Auth !== "undefined") {
        Auth.limpiar();
      } else {
        localStorage.clear();
        sessionStorage.clear();
      }
      window.location.href = "../login.html";
    });
  }

  if (btnNotify) {
    btnNotify.addEventListener("click", () => {
      alert("Evaluaciones y actividades pendientes:\n1. Práctica calificada 1 (Fundamentos de Programación con Python)\n2. Examen de HTML y CSS\n3. Diseño del modelo entidad-relación (MySQL)\n4. Examen de consultas SQL (MySQL)");
    });
  }

  // Inicializar vista
  renderizarCursos();
  actualizarStats();
  actualizarGrafico();
  await cargarUsuarioSesion();
});
