// Lógica unificada para Mis Calificaciones
// Estrategia Híbrida: Conexión prioritaria a BD MySQL (/api/cursos y /api/cursos/{id}/mis-notas) + Respaldo de plantilla simulada

document.addEventListener("DOMContentLoaded", async () => {
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

  const studentNameEl = document.getElementById("student-name");
  const studentRoleEl = document.getElementById("student-role");
  const tbody = document.getElementById("calificaciones-tbody");
  const detalleContainer = document.getElementById("detalle-evaluaciones-container");
  const btnLogout = document.getElementById("btn-logout");

  // PARTE 2: Plantilla de Respaldo Simulada (Mantiene compatibilidad con análisis de la delegada)
  const DATA_CURSOS_SIMULADOS = [
    {
      id: 1,
      codigo: "PRG-101",
      nombre: "Fundamentos de Programación con Python",
      periodo: "2026-II",
      promedio: 14.0,
      origenDatos: "simulado",
      evaluaciones: [
        { nombre: "Tarea 1: Variables y tipos", fecha: "10/10/2026", peso: "20%", nota: "14.00", estado: "Calificado" },
        { nombre: "Práctica calificada 1", fecha: "24/10/2026", peso: "30%", nota: "—", estado: "Pendiente" },
        { nombre: "Examen parcial", fecha: "14/11/2026", peso: "50%", nota: "—", estado: "Pendiente" }
      ]
    },
    {
      id: 2,
      codigo: "WEB-101",
      nombre: "HTML y CSS",
      periodo: "2026-II",
      promedio: 14.0,
      origenDatos: "simulado",
      evaluaciones: [
        { nombre: "Proyecto: página personal", fecha: "15/10/2026", peso: "40%", nota: "14.00", estado: "Calificado" },
        { nombre: "Examen de HTML y CSS", fecha: "05/11/2026", peso: "60%", nota: "—", estado: "Pendiente" }
      ]
    },
    {
      id: 3,
      codigo: "WEB-201",
      nombre: "JavaScript",
      periodo: "2026-II",
      promedio: 15.0,
      origenDatos: "simulado",
      evaluaciones: [
        { nombre: "Laboratorio 1: DOM y Eventos", fecha: "18/10/2026", peso: "30%", nota: "15.00", estado: "Calificado" },
        { nombre: "Proyecto: Aplicación interactiva", fecha: "12/11/2026", peso: "70%", nota: "—", estado: "Pendiente" }
      ]
    },
    {
      id: 4,
      codigo: "BD-101",
      nombre: "Bases de Datos con MySQL",
      periodo: "2026-II",
      promedio: 14.0,
      origenDatos: "simulado",
      evaluaciones: [
        { nombre: "Diseño del modelo entidad-relación", fecha: "20/10/2026", peso: "40%", nota: "—", estado: "Pendiente" },
        { nombre: "Examen de consultas SQL", fecha: "10/11/2026", peso: "60%", nota: "—", estado: "Pendiente" }
      ]
    }
  ];

  let cursos = [...DATA_CURSOS_SIMULADOS];

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
  // PARTE 1: CARGA DE CALIFICACIONES REALES DESDE LA BD (CON FALLBACK)
  // =========================================================================
  async function cargarCalificacionesHibridas() {
    if (typeof Auth === "undefined" || !Auth.token()) {
      renderizarCalificaciones();
      return;
    }

    try {
      const resCursos = await Auth.fetchAutenticado("/api/cursos");
      if (!resCursos || !resCursos.ok) {
        renderizarCalificaciones();
        return;
      }

      const listaCursos = await resCursos.json();
      if (!Array.isArray(listaCursos) || listaCursos.length === 0) {
        renderizarCalificaciones();
        return;
      }

      const cursosProcesados = await Promise.all(listaCursos.map(async (c) => {
        const codigo = c.codigo || "CURSO";
        let filasBD = [];
        let promedioBD = null;

        try {
          const resNotas = await Auth.fetchAutenticado(`/api/cursos/${c.id}/mis-notas`);
          if (resNotas && resNotas.ok) {
            const dataNotas = await resNotas.json();
            filasBD = dataNotas.filas || [];
            promedioBD = dataNotas.promedio_actual;
          }
        } catch (errNotas) {
          console.warn(`Error al consultar notas para curso ${c.id}:`, errNotas);
        }

        // Si existen evaluaciones y notas registradas en MySQL para este curso
        if (filasBD.length > 0) {
          const promCalculado = promedioBD !== null && promedioBD !== undefined ? Number(promedioBD) : 14.0;
          return {
            id: c.id,
            codigo: codigo,
            nombre: limpiarTexto(c.nombre),
            periodo: "2026-II",
            promedio: promCalculado,
            origenDatos: "bd",
            evaluaciones: filasBD.map(f => {
              const valorNota = f.nota !== null && f.nota !== undefined ? Number(f.nota).toFixed(2) : "—";
              const estadoLimpio = f.estado ? f.estado.charAt(0).toUpperCase() + f.estado.slice(1).toLowerCase() : (f.nota !== null ? "Calificado" : "Pendiente");
              return {
                nombre: limpiarTexto(f.nombre),
                fecha: f.fecha_vencimiento ? new Date(f.fecha_vencimiento).toLocaleDateString("es-PE") : "Programada",
                peso: `${Math.round(f.peso)}%`,
                nota: valorNota,
                estado: estadoLimpio
              };
            })
          };
        }

        // Si no hay notas en BD para este curso, buscar si existe plantilla simulada
        const fallback = DATA_CURSOS_SIMULADOS.find(s => s.codigo === codigo || s.id === c.id);
        if (fallback) {
          return { ...fallback, id: c.id, nombre: limpiarTexto(c.nombre) };
        }

        // Caso base si es un curso nuevo sin notas
        return {
          id: c.id,
          codigo: codigo,
          nombre: limpiarTexto(c.nombre),
          periodo: "2026-II",
          promedio: 14.0,
          origenDatos: "simulado",
          evaluaciones: [
            { nombre: "Evaluación Continua 1", fecha: "Ciclo 2026", peso: "50%", nota: "—", estado: "Pendiente" },
            { nombre: "Examen Final", fecha: "Ciclo 2026", peso: "50%", nota: "—", estado: "Pendiente" }
          ]
        };
      }));

      if (cursosProcesados.length > 0) {
        cursos = cursosProcesados;
      }
    } catch (e) {
      console.warn("Fallo cargando notas de BD, usando datos simulados de respaldo:", e);
      cursos = [...DATA_CURSOS_SIMULADOS];
    }

    renderizarCalificaciones();
  }

  function renderizarCalificaciones() {
    if (!tbody || !detalleContainer) return;
    tbody.replaceChildren();
    detalleContainer.replaceChildren();

    cursos.forEach(c => {
      const nombreLimpio = limpiarTexto(c.nombre);
      const totalEval = c.evaluaciones.length;
      const calificadas = c.evaluaciones.filter(e => e.estado === "Calificado" || e.nota !== "—").length;
      const esAprobado = c.promedio >= 11;
      const esDatoReal = c.origenDatos === "bd";

      // Fila en tabla resumen
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>
          <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
            <strong style="color: #0f172a; font-size: 13.5px;">${nombreLimpio}</strong>
            ${esDatoReal ? '<span class="badge-status badge-status-present" style="background:#f0fdf4;color:#16a34a;border:1px solid #bbf7d0;font-size:10.5px;padding:2px 6px;">✓ BD Real</span>' : '<span class="badge-status" style="background:#f8fafc;color:#64748b;border:1px solid #e2e8f0;font-size:10.5px;padding:2px 6px;">Simulado</span>'}
          </div>
          <small style="color: #64748b;">${c.codigo} · ${c.periodo}</small>
        </td>
        <td>
          <span style="font-weight: 600;">${calificadas} de ${totalEval} calificadas</span>
        </td>
        <td>
          <strong style="font-size: 15px; color: ${esAprobado ? '#15803d' : '#b91c1c'};">${c.promedio.toFixed(1)}</strong>
        </td>
        <td>
          <span class="badge-status ${esAprobado ? 'badge-status-present' : 'badge-status-absent'}">
            ● ${esAprobado ? 'Aprobado' : 'Desaprobado'}
          </span>
        </td>
        <td style="text-align: right;">
          <a href="#card-detalle-${c.id}" class="btn-secundario" style="font-size: 11.5px; padding: 6px 12px; text-decoration: none;">
            Ver evaluaciones ▾
          </a>
        </td>
      `;
      tbody.appendChild(tr);

      // Tarjeta de detalle de evaluaciones
      const card = document.createElement("div");
      card.className = "dash-card";
      card.id = `card-detalle-${c.id}`;

      card.innerHTML = `
        <div class="section-top-header" style="margin-bottom: 14px;">
          <div class="section-title-wrap">
            <div style="display: flex; align-items: center; gap: 8px;">
              <h3 style="font-size: 16px; font-weight: 800; color: #0f172a;">${nombreLimpio} (${c.codigo})</h3>
              ${esDatoReal ? '<span class="badge-status badge-status-present" style="background:#f0fdf4;color:#16a34a;border:1px solid #bbf7d0;font-size:11px;">✓ Base de Datos MySQL</span>' : '<span class="badge-status" style="background:#f8fafc;color:#64748b;border:1px solid #e2e8f0;font-size:11px;">Datos Simulados</span>'}
            </div>
            <p style="font-size: 12px; color: #64748b;">Desglose de evaluaciones continuas y ponderación</p>
          </div>
          <div>
            <span class="badge-status ${esAprobado ? 'badge-status-present' : 'badge-status-absent'}" style="font-size: 12px;">
              Promedio: <strong>${c.promedio.toFixed(1)}</strong>
            </span>
          </div>
        </div>

        <div class="dash-table-wrap">
          <table class="dash-table">
            <thead>
              <tr>
                <th>Evaluación</th>
                <th>Fecha programada</th>
                <th>Ponderación</th>
                <th>Calificación</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              ${c.evaluaciones.map(ev => `
                <tr>
                  <td><strong>${limpiarTexto(ev.nombre)}</strong></td>
                  <td>${ev.fecha}</td>
                  <td><span style="font-weight: 600; color: #2563eb;">${ev.peso}</span></td>
                  <td>
                    <strong style="font-size: 14px; color: ${ev.nota !== '—' ? '#15803d' : '#64748b'};">
                      ${ev.nota}
                    </strong>
                  </td>
                  <td>
                    <span class="badge-status ${ev.estado === 'Calificado' ? 'badge-status-present' : 'badge-status-late'}">
                      ● ${ev.estado}
                    </span>
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `;

      detalleContainer.appendChild(card);
    });
  }

  if (btnLogout) {
    btnLogout.addEventListener("click", () => {
      if (typeof Auth !== "undefined") Auth.limpiar();
      window.location.href = "../login.html";
    });
  }

  // Iniciar flujo híbrido
  await cargarCalificacionesHibridas();
});
