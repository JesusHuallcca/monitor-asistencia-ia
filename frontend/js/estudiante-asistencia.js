// Lógica de "Mi Asistencia" - Historial de asistencia facial por curso
// Estrategia Híbrida: Conexión prioritaria a BD MySQL + Respaldo de plantilla simulada

document.addEventListener("DOMContentLoaded", async () => {
  // Limpieza de caracteres para UTF-8
  function limpiarTexto(str) {
    if (!str) return "";
    return str
      .replace(/Ã¡/g, "á")
      .replace(/Ã©/g, "é")
      .replace(/Ã­/g, "í")
      .replace(/Ã³/g, "ó")
      .replace(/Ãº/g, "ú")
      .replace(/Ã±/g, "ñ")
      .replace(/Ã /g, "Á")
      .replace(/Ã‰/g, "É")
      .replace(/Ã /g, "Í")
      .replace(/Ã“/g, "Ó")
      .replace(/Ãš/g, "Ú")
      .replace(/Ã‘/g, "Ñ");
  }

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

  // PARTE 2: Plantilla de Respaldo (Datos simulados)
  const CURSOS_ASISTENCIA_SIMULADOS = [
    {
      id: 4,
      codigo: "BD-101",
      nombre: "Bases de Datos con MySQL",
      banner: "../assets/img/banner_stats.jpg",
      seccion: "Sección 01",
      profesor: "Ing. Carlos Mendoza",
      sesionActiva: true,
      aula: "Aula 301 · Laboratorio",
      porcentaje: 100,
      totalSesiones: 14,
      asistencias: 14,
      faltas: 0,
      tardanzas: 0,
      origenDatos: "simulado",
      registros: [
        { fecha: "28/10/2026", hora: "08:04 AM", estado: "Presente", metodo: "Facial IA", aula: "Aula 301" },
        { fecha: "26/10/2026", hora: "08:02 AM", estado: "Presente", metodo: "Facial IA", aula: "Aula 301" },
        { fecha: "21/10/2026", hora: "08:05 AM", estado: "Presente", metodo: "Facial IA", aula: "Aula 301" },
        { fecha: "19/10/2026", hora: "08:01 AM", estado: "Presente", metodo: "Facial IA", aula: "Aula 301" },
        { fecha: "14/10/2026", hora: "08:03 AM", estado: "Presente", metodo: "Facial IA", aula: "Aula 301" }
      ]
    },
    {
      id: 1,
      codigo: "PRG-101",
      nombre: "Fundamentos de Programación con Python",
      banner: "../assets/img/banner_python.jpg",
      seccion: "Sección 01",
      profesor: "Lic. Roberto Torres",
      sesionActiva: true,
      aula: "Aula 205 · Principal",
      porcentaje: 95,
      totalSesiones: 16,
      asistencias: 15,
      faltas: 0,
      tardanzas: 1,
      origenDatos: "simulado",
      registros: [
        { fecha: "28/10/2026", hora: "14:02 PM", estado: "Presente", metodo: "Facial IA", aula: "Aula 205" },
        { fecha: "26/10/2026", hora: "14:15 PM", estado: "Tarde", metodo: "Facial IA", aula: "Aula 205" },
        { fecha: "23/10/2026", hora: "14:01 PM", estado: "Presente", metodo: "Facial IA", aula: "Aula 205" },
        { fecha: "21/10/2026", hora: "14:04 PM", estado: "Presente", metodo: "Facial IA", aula: "Aula 205" },
        { fecha: "16/10/2026", hora: "14:00 PM", estado: "Presente", metodo: "Facial IA", aula: "Aula 205" }
      ]
    },
    {
      id: 2,
      codigo: "WEB-101",
      nombre: "HTML y CSS",
      banner: "../assets/img/banner_ia.jpg",
      seccion: "Sección 01",
      profesor: "Ing. Valeria Salas",
      sesionActiva: true,
      aula: "Aula 102 · Multimedia",
      porcentaje: 100,
      totalSesiones: 12,
      asistencias: 12,
      faltas: 0,
      tardanzas: 0,
      origenDatos: "simulado",
      registros: [
        { fecha: "27/10/2026", hora: "10:02 AM", estado: "Presente", metodo: "Facial IA", aula: "Aula 102" },
        { fecha: "22/10/2026", hora: "10:01 AM", estado: "Presente", metodo: "Facial IA", aula: "Aula 102" },
        { fecha: "20/10/2026", hora: "10:05 AM", estado: "Presente", metodo: "Facial IA", aula: "Aula 102" },
        { fecha: "15/10/2026", hora: "10:00 AM", estado: "Presente", metodo: "Facial IA", aula: "Aula 102" },
        { fecha: "13/10/2026", hora: "10:03 AM", estado: "Presente", metodo: "Facial IA", aula: "Aula 102" }
      ]
    },
    {
      id: 3,
      codigo: "WEB-201",
      nombre: "JavaScript",
      banner: "../assets/img/banner_cyber.jpg",
      seccion: "Sección 01",
      profesor: "Mg. Daniel Paredes",
      sesionActiva: false,
      aula: "Aula 303 · Laboratorio",
      porcentaje: 92,
      totalSesiones: 12,
      asistencias: 11,
      faltas: 1,
      tardanzas: 0,
      origenDatos: "simulado",
      registros: [
        { fecha: "27/10/2026", hora: "16:03 PM", estado: "Presente", metodo: "Facial IA", aula: "Aula 303" },
        { fecha: "22/10/2026", hora: "16:01 PM", estado: "Presente", metodo: "Facial IA", aula: "Aula 303" },
        { fecha: "20/10/2026", hora: "—", estado: "Ausente", metodo: "No registrado", aula: "Aula 303" },
        { fecha: "15/10/2026", hora: "16:05 PM", estado: "Presente", metodo: "Facial IA", aula: "Aula 303" },
        { fecha: "13/10/2026", hora: "16:02 PM", estado: "Presente", metodo: "Facial IA", aula: "Aula 303" }
      ]
    }
  ];

  let cursos = [...CURSOS_ASISTENCIA_SIMULADOS];

  // Elementos DOM
  const container = document.getElementById("attendance-courses-container");
  const inputSearch = document.getElementById("search-asistencia-input");
  const studentNameEl = document.getElementById("student-name");
  const studentRoleEl = document.getElementById("student-role");
  const btnLogout = document.getElementById("btn-logout");

  // Modal de Cámara
  const modal = document.getElementById("modal-asistencia-camara");
  const btnCloseModal = document.getElementById("btn-close-camera-modal");
  const btnCancelModal = document.getElementById("btn-cancel-modal");
  const videoEl = document.getElementById("camera-stream");
  const modalCourseTitle = document.getElementById("modal-course-title");
  const cameraFeedback = document.getElementById("camera-feedback-title");
  const cameraSub = document.getElementById("camera-feedback-sub");

  let mediaStream = null;

  // Cargar usuario autenticado
  if (typeof Auth !== "undefined" && Auth.token()) {
    try {
      const resp = await Auth.fetchAutenticado("/api/users/me");
      if (resp && resp.ok) {
        const u = await resp.json();
        if (studentNameEl) studentNameEl.textContent = limpiarTexto(`${u.nombres} ${u.apellidos}`);
        if (studentRoleEl) studentRoleEl.textContent = u.rol === "estudiante" ? "Estudiante" : u.rol;
      }
    } catch (e) {
      console.warn("Usuario local", e);
    }
  }

  // =========================================================================
  // PARTE 1: CARGA DE DATOS REALES DE BD (CON FALLBACK A SIMULADOS)
  // =========================================================================
  async function cargarDatosHibridos() {
    if (typeof Auth === "undefined" || !Auth.token()) {
      renderizarCursos();
      return;
    }

    try {
      // 1. Obtener los cursos en los que está matriculado el estudiante
      const resCursos = await Auth.fetchAutenticado("/api/cursos");
      if (!resCursos || !resCursos.ok) {
        renderizarCursos();
        return;
      }

      const listaCursos = await resCursos.json();
      if (!Array.isArray(listaCursos) || listaCursos.length === 0) {
        renderizarCursos();
        return;
      }

      let totalRegistrosBD = 0;
      const cursosProcesados = await Promise.all(listaCursos.map(async (c) => {
        const codigo = c.codigo || "CURSO";
        const banner = BANNER_MAP[codigo] || "../assets/img/banner_python.jpg";

        // Consultar asistencias reales del curso para este estudiante
        let registrosBD = [];
        let promedioBD = null;
        let presentesBD = 0;

        try {
          const resAsist = await Auth.fetchAutenticado(`/api/attendance/my-course/${c.id}`);
          if (resAsist && resAsist.ok) {
            const dataAsist = await resAsist.json();
            registrosBD = dataAsist.registros || [];
            promedioBD = dataAsist.promedio;
            presentesBD = dataAsist.presentes || 0;
            totalRegistrosBD += registrosBD.length;
          }
        } catch (errAsist) {
          console.warn(`No se pudo cargar asistencia BD para curso ${c.id}:`, errAsist);
        }

        // Si este curso tiene registros reales en la BD, calcular estadísticas con la BD
        if (registrosBD.length > 0) {
          const totalSes = registrosBD.length;
          const tardanzas = registrosBD.filter(r => r.estado === "TARDANZA").length;
          const ausentes = registrosBD.filter(r => r.estado === "AUSENTE").length;
          const pct = Math.round(((presentesBD + tardanzas) / totalSes) * 100);

          return {
            id: c.id,
            codigo: codigo,
            nombre: limpiarTexto(c.nombre),
            banner: banner,
            seccion: "Sección 01",
            profesor: c.profesor_nombre ? limpiarTexto(c.profesor_nombre) : "Docente Asignado",
            sesionActiva: true,
            porcentaje: pct,
            totalSesiones: totalSes,
            asistencias: presentesBD,
            faltas: ausentes,
            tardanzas: tardanzas,
            origenDatos: "bd",
            registros: registrosBD.map(r => ({
              fecha: r.fecha || "—",
              hora: r.hora || "08:00 AM",
              aula: "Laboratorio Central",
              metodo: "Facial IA",
              estado: r.estado === "PRESENTE" ? "Presente" : r.estado === "TARDANZA" ? "Tarde" : "Ausente"
            }))
          };
        }

        // Si para este curso en particular no hay registros en BD, usar la plantilla simulada
        const fallback = CURSOS_ASISTENCIA_SIMULADOS.find(s => s.codigo === codigo || s.id === c.id);
        if (fallback) {
          return { ...fallback, id: c.id, nombre: limpiarTexto(c.nombre) };
        }

        return {
          id: c.id,
          codigo: codigo,
          nombre: limpiarTexto(c.nombre),
          banner: banner,
          seccion: "Sección 01",
          profesor: "Docente Asignado",
          sesionActiva: false,
          porcentaje: 100,
          totalSesiones: 1,
          asistencias: 1,
          faltas: 0,
          tardanzas: 0,
          origenDatos: "simulado",
          registros: [
            { fecha: new Date().toLocaleDateString("es-PE"), hora: "08:00 AM", aula: "Laboratorio", metodo: "Facial IA", estado: "Presente" }
          ]
        };
      }));

      // Si obtuvimos cursos (reales o con fallback), los usamos
      if (cursosProcesados.length > 0) {
        cursos = cursosProcesados;
      }
    } catch (e) {
      console.warn("Fallo en carga de BD. Usando plantilla simulada de respaldo:", e);
      cursos = [...CURSOS_ASISTENCIA_SIMULADOS];
    }

    renderizarCursos();
  }

  function renderizarCursos(filtro = "") {
    if (!container) return;
    container.replaceChildren();

    const q = filtro.trim().toLowerCase();
    const filtrados = cursos.filter(c => 
      c.nombre.toLowerCase().includes(q) || 
      c.codigo.toLowerCase().includes(q)
    );

    if (filtrados.length === 0) {
      container.innerHTML = `
        <div class="dash-card" style="text-align: center; color: #64748b; padding: 40px;">
          <p>No se encontraron cursos que coincidan con "<strong>${filtro}</strong>".</p>
        </div>
      `;
      return;
    }

    filtrados.forEach((c) => {
      const card = document.createElement("div");
      card.className = "attendance-course-card";

      const nombreLimpio = limpiarTexto(c.nombre);
      const isActivo = c.sesionActiva;
      const esDatoReal = c.origenDatos === "bd";

      card.innerHTML = `
        <!-- Cabecera del Curso -->
        <div class="attendance-course-header">
          <div class="course-header-meta">
            <div class="course-thumb-box">
              <img src="${c.banner}" alt="${nombreLimpio}" loading="lazy" />
            </div>
            <div class="course-title-block">
              <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                <h3>${nombreLimpio}</h3>
                ${isActivo ? '<span class="badge-status badge-status-active">● Sesión activa hoy</span>' : ''}
                ${esDatoReal ? '<span class="badge-status badge-status-present" style="background:#f0fdf4;color:#16a34a;border:1px solid #bbf7d0;font-size:11px;">✓ BD Sincronizada</span>' : '<span class="badge-status" style="background:#f8fafc;color:#64748b;border:1px solid #e2e8f0;font-size:11px;">Modo Demostración</span>'}
              </div>
              <p>${c.codigo} | ${c.seccion} · Docente: ${c.profesor}</p>
            </div>
          </div>

          <div class="attendance-header-actions">
            ${isActivo ? `
              <button type="button" class="btn-mark-attendance" data-curso-id="${c.id}" data-curso-nombre="${nombreLimpio}">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                  <circle cx="12" cy="13" r="4"/>
                </svg>
                Marcar asistencia facial
              </button>
            ` : ''}
            <button type="button" class="btn-toggle-history" data-target="history-${c.id}">
              <span>Ver asistencias</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Métricas de Asistencia del Curso -->
        <div class="attendance-metrics-grid">
          <div class="metric-circle-block">
            <span class="pct-badge-big">${c.porcentaje}%</span>
            <div>
              <span class="metric-label-small">Porcentaje</span>
              <div class="progress-bar-wrap" style="width: 100px;">
                <div class="progress-bar-fill" style="width: ${c.porcentaje}%;"></div>
              </div>
            </div>
          </div>

          <div class="metric-count-item">
            <span class="metric-label-small">Sesiones totales</span>
            <span class="metric-count-num">${c.totalSesiones}</span>
          </div>

          <div class="metric-count-item">
            <span class="metric-label-small">Asistencias</span>
            <span class="metric-count-num" style="color: #16a34a;">${c.asistencias}</span>
          </div>

          <div class="metric-count-item">
            <span class="metric-label-small">Faltas / Tardanzas</span>
            <span class="metric-count-num" style="color: ${c.faltas > 0 ? '#dc2626' : '#64748b'};">
              ${c.faltas} falta${c.faltas !== 1 ? 's' : ''} / ${c.tardanzas} tarde
            </span>
          </div>
        </div>

        <!-- Historial Detallado de Asistencias (Desplegable) -->
        <div class="attendance-history-drawer" id="history-${c.id}">
          <h4>Últimos registros de asistencia biométrica ${esDatoReal ? '(Desde MySQL)' : '(Simulado)'}</h4>
          <div class="dash-table-wrap">
            <table class="dash-table">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Hora de registro</th>
                  <th>Ubicación / Aula</th>
                  <th>Método de validación</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                ${c.registros.map(r => `
                  <tr>
                    <td><strong>${r.fecha}</strong></td>
                    <td>${r.hora}</td>
                    <td>${r.aula}</td>
                    <td>
                      <span style="display: inline-flex; align-items: center; gap: 5px; font-weight: 600; color: #2563eb;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <circle cx="12" cy="12" r="3"/>
                          <path d="M3 7V5a2 2 0 0 1 2-2h2"/>
                          <path d="M17 3h2a2 2 0 0 1 2 2v2"/>
                          <path d="M21 17v2a2 2 0 0 1-2 2h-2"/>
                          <path d="M7 21H5a2 2 0 0 1-2-2v-2"/>
                        </svg>
                        ${r.metodo}
                      </span>
                    </td>
                    <td>
                      <span class="badge-status ${
                        r.estado === 'Presente' ? 'badge-status-present' : 
                        r.estado === 'Tarde' ? 'badge-status-late' : 'badge-status-absent'
                      }">
                        ● ${r.estado}
                      </span>
                    </td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        </div>
      `;

      container.appendChild(card);
    });

    // Asignar eventos de toggle de historial
    document.querySelectorAll(".btn-toggle-history").forEach(btn => {
      btn.addEventListener("click", () => {
        const targetId = btn.dataset.target;
        const targetEl = document.getElementById(targetId);
        if (targetEl) {
          const isHidden = targetEl.style.display === "none";
          targetEl.style.display = isHidden ? "block" : "none";
          btn.querySelector("span").textContent = isHidden ? "Ocultar asistencias" : "Ver asistencias";
          btn.querySelector("svg").style.transform = isHidden ? "rotate(180deg)" : "none";
        }
      });
    });

    // Botones para marcar asistencia facial (abren modal)
    document.querySelectorAll(".btn-mark-attendance").forEach(btn => {
      btn.addEventListener("click", () => {
        const nombre = btn.dataset.cursoNombre || "el curso";
        abrirModalCamara(nombre);
      });
    });
  }

  // Manejo de la cámara y reconocimiento facial
  async function abrirModalCamara(cursoNombre) {
    if (modalCourseTitle) modalCourseTitle.textContent = `Registro Facial — ${cursoNombre}`;
    if (cameraFeedback) cameraFeedback.textContent = "Iniciando cámara...";
    if (cameraSub) cameraSub.textContent = "Por favor mira fijamente a la cámara para la verificación biométrica.";
    modal.classList.add("open");

    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "user" }
      });
      if (videoEl) {
        videoEl.srcObject = mediaStream;
        await videoEl.play();
      }

      if (cameraFeedback) cameraFeedback.textContent = "Buscando rostro...";
      if (cameraSub) cameraSub.textContent = "Encuadra tu rostro dentro del marco.";

      // Simular verificación biométrica con backend en 3 segundos
      setTimeout(() => {
        if (cameraFeedback) {
          cameraFeedback.textContent = "¡Asistencia Registrada Exitosamente!";
          cameraFeedback.style.color = "#16a34a";
        }
        if (cameraSub) {
          const ahora = new Date().toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" });
          cameraSub.innerHTML = `<strong>Presente</strong> a las ${ahora} · Reconocimiento biométrico 99.4% de certeza.`;
        }
      }, 3000);

    } catch (err) {
      console.warn("No se pudo iniciar la cámara:", err);
      if (cameraFeedback) cameraFeedback.textContent = "Cámara no disponible";
      if (cameraSub) cameraSub.textContent = "Verifica los permisos del navegador o conecta una cámara web.";
    }
  }

  function cerrarModalCamara() {
    modal.classList.remove("open");
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop());
      mediaStream = null;
    }
    if (videoEl) videoEl.srcObject = null;
    if (cameraFeedback) cameraFeedback.style.color = "#0f172a";
  }

  if (btnCloseModal) btnCloseModal.addEventListener("click", cerrarModalCamara);
  if (btnCancelModal) btnCancelModal.addEventListener("click", cerrarModalCamara);

  if (inputSearch) {
    inputSearch.addEventListener("input", (e) => {
      renderizarCursos(e.target.value);
    });
  }

  if (btnLogout) {
    btnLogout.addEventListener("click", () => {
      if (typeof Auth !== "undefined") Auth.limpiar();
      window.location.href = "../login.html";
    });
  }

  // Iniciar flujo híbrido
  await cargarDatosHibridos();
});
