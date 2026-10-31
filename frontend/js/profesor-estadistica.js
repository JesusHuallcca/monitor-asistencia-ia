// Lógica de visualización para Estadística Básica (Parte 1) - Panel de Profesor

document.addEventListener("DOMContentLoaded", async () => {
  const yo = await Panel.iniciar("profesor");
  if (!yo) return;

  const btnActualizar = document.getElementById("btn-actualizar-stats");
  const estadoActualizacion = document.getElementById("estado-actualizacion");
  const imgGrafico = document.getElementById("img-grafico-estadistico");
  const contenedorEmociones = document.getElementById("contenedor-emociones-tabla");

  // Elementos KPI
  const kpiProbAsistencia = document.getElementById("kpi-prob-asistencia");
  const kpiProbInasistencia = document.getElementById("kpi-prob-inasistencia");
  const kpiTotalRegistros = document.getElementById("kpi-total-registros");
  const kpiTotalEmociones = document.getElementById("kpi-total-emociones");
  const kpiUltimaAct = document.getElementById("kpi-ultima-actualizacion");

  const EMO_NOMBRES = {
    happy: "Felicidad (Happy)",
    sad: "Tristeza (Sad)",
    angry: "Enojo (Angry)",
    neutral: "Neutralidad (Neutral)",
    surprise: "Sorpresa (Surprise)",
    fear: "Temor (Fear)",
    disgust: "Disgusto (Disgust)"
  };

  async function cargarEstadisticas() {
    try {
      const resp = await Panel.api("/api/estadistica/kpis");
      if (!resp.ok) {
        if (resp.status === 404) {
          Panel.avisar("Aún no se ha generado el reporte estadístico. Haz clic en 'Actualizar estadísticas' para generarlo.", "info");
        } else {
          Panel.avisar("No se pudieron cargar los KPIs estadísticos.", "error");
        }
        return;
      }

      const datos = await resp.json();

      // Renderizar KPIs
      const asis = datos.asistencia || {};
      const probAsisPct = (asis.probabilidad_asistencia * 100).toFixed(1);
      const probInasPct = (asis.probabilidad_inasistencia * 100).toFixed(1);

      if (kpiProbAsistencia) kpiProbAsistencia.textContent = `${probAsisPct}%`;
      if (kpiProbInasistencia) kpiProbInasistencia.textContent = `${probInasPct}%`;
      if (kpiTotalRegistros) kpiTotalRegistros.textContent = asis.total_registros?.toLocaleString() || "0";
      if (kpiTotalEmociones) kpiTotalEmociones.textContent = datos.calidad_datos?.registros_emociones?.toLocaleString() || "0";

      if (kpiUltimaAct && datos.ultima_actualizacion) {
        const d = new Date(datos.ultima_actualizacion);
        kpiUltimaAct.textContent = `Actualizado: ${d.toLocaleDateString("es-PE")} ${d.toLocaleTimeString("es-PE")}`;
      }

      // Renderizar gráfico mediante API autenticada
      if (imgGrafico) {
        try {
          const respImg = await Panel.api(`/api/estadistica/grafico?t=${Date.now()}`);
          if (respImg.ok) {
            const blob = await respImg.blob();
            imgGrafico.src = URL.createObjectURL(blob);
            imgGrafico.style.display = "block";
          }
        } catch (errImg) {
          console.error("Error al cargar imagen del gráfico:", errImg);
        }
      }

      // Renderizar tabla de emociones
      if (contenedorEmociones && datos.emociones) {
        contenedorEmociones.replaceChildren();
        Object.entries(datos.emociones).forEach(([key, val]) => {
          const tr = document.createElement("tr");
          const mediaPct = (val.media * 100).toFixed(2);
          const desvPct = (val.desviacion * 100).toFixed(2);

          tr.innerHTML = `
            <td><strong>${EMO_NOMBRES[key] || key}</strong></td>
            <td><strong style="color: #2563eb;">${val.media?.toFixed(4)}</strong> (${mediaPct}%)</td>
            <td>±${val.desviacion?.toFixed(4)} (${desvPct}%)</td>
            <td>${val.n?.toLocaleString() || "—"}</td>
            <td>
              <div style="width: 100%; height: 6px; background-color: #e2e8f0; border-radius: 99px; overflow: hidden;">
                <div style="width: ${Math.min(100, Math.max(5, mediaPct * 2))}%; height: 100%; background-color: #3b82f6; border-radius: 99px;"></div>
              </div>
            </td>
          `;
          contenedorEmociones.appendChild(tr);
        });
      }

    } catch (err) {
      console.error("Error al cargar estadísticas:", err);
      Panel.avisar("Error de conexión al cargar estadísticas.", "error");
    }
  }

  // Botón para actualizar estadísticas en caliente
  if (btnActualizar) {
    btnActualizar.addEventListener("click", async () => {
      btnActualizar.disabled = true;
      btnActualizar.textContent = "⏳ Recalculando con IA...";
      if (estadoActualizacion) {
        estadoActualizacion.textContent = "Ejecutando análisis batch en segundo plano...";
        estadoActualizacion.style.color = "#2563eb";
      }

      try {
        const resp = await Panel.api("/api/estadistica/actualizar", {
          method: "POST"
        });

        if (resp.ok) {
          const resultado = await resp.json();
          Panel.avisar("¡Estadísticas recalculadas exitosamente!", "exito");
          if (estadoActualizacion) {
            estadoActualizacion.textContent = "✓ Reporte y gráficos actualizados.";
            estadoActualizacion.style.color = "#16a34a";
          }
          await cargarEstadisticas();
        } else {
          const err = await resp.json().catch(() => ({}));
          Panel.avisar(err.detail || "Error al recalcular estadísticas.", "error");
          if (estadoActualizacion) {
            estadoActualizacion.textContent = "Error durante el recálculo.";
            estadoActualizacion.style.color = "#b91c1c";
          }
        }
      } catch (e) {
        Panel.avisar("Fallo de comunicación con el servidor.", "error");
      } finally {
        btnActualizar.disabled = false;
        btnActualizar.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          Actualizar estadísticas en vivo
        `;
      }
    });
  }

  await cargarEstadisticas();
});

