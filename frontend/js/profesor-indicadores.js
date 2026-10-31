// Lógica del Dashboard Ejecutivo de Indicadores ML (Parte 5)
// Panel del Profesor - Senati

document.addEventListener("DOMContentLoaded", async () => {
  // Inicializa el layout del panel profesor, valida sesión e inyecta el sidebar oficial
  const yo = await Panel.iniciar("profesor");
  if (!yo) return;

  let chartTendencia = null;
  let chartEmo = null;

  async function cargarDashboard() {
    try {
      const resp = await Panel.api("/api/ml/indicadores");
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      // 1. Fechas y Encabezados
      const badgeFecha = document.getElementById("badge-fecha-consulta");
      if (badgeFecha && data.fecha_consulta) {
        badgeFecha.textContent = `${data.periodo || "Ciclo 2026-I"} · ${data.fecha_consulta}`;
      }
      const txtPeriodo = document.getElementById("txt-periodo-empresa");
      if (txtPeriodo && data.empresa) {
        txtPeriodo.textContent = `${data.empresa} · ${data.periodo || ""}`;
      }

      // 2. Tarjetas Rápidas de KPIs
      const kpis = data.kpis_rapidos || [];
      kpis.forEach(k => {
        if (k.id === "media") {
          const el = document.getElementById("kpi-media-val");
          if (el) el.textContent = k.valor;
        } else if (k.id === "prediccion") {
          const el = document.getElementById("kpi-pred-val");
          if (el) el.textContent = k.valor;
        } else if (k.id === "segmento") {
          const el = document.getElementById("kpi-seg-val");
          if (el) el.textContent = k.valor;
        } else if (k.id === "sesiones") {
          const el = document.getElementById("kpi-ses-val");
          if (el) el.textContent = k.valor;
        }
      });

      // 3. Predicción Supervisada (Regresión)
      const p = data.prediccion_regresion || {};
      const txtPredScore = document.getElementById("txt-pred-score");
      if (txtPredScore) txtPredScore.textContent = p.valor_porcentaje || `${Math.round(p.valor || 81)}%`;

      const txtIntervalo = document.getElementById("txt-pred-intervalo");
      if (txtIntervalo) txtIntervalo.textContent = p.intervalo_confianza || "75% – 87%";

      const badgeR2 = document.getElementById("badge-r2-modelo");
      if (badgeR2 && p.r2 != null) badgeR2.textContent = `R² = ${(p.r2 * 100).toFixed(1)}%`;

      const txtPredInterp = document.getElementById("txt-pred-interpretacion");
      if (txtPredInterp && p.interpretacion) txtPredInterp.textContent = p.interpretacion;

      const contFeatures = document.getElementById("contenedor-features-tags");
      if (contFeatures && Array.isArray(p.features_usadas)) {
        contFeatures.innerHTML = p.features_usadas
          .map(f => `<span class="tag-pill" style="background:#f1f5f9; color:#334155;">${f}</span>`)
          .join("");
      }

      // 4. Segmentación K-Means
      const seg = data.segmentacion || {};
      const contSegBarras = document.getElementById("contenedor-segmentos-barras");
      if (contSegBarras && Array.isArray(seg.distribucion)) {
        const coloresSeg = ["#f97316", "#f59e0b", "#10b981", "#8b5cf6"];
        contSegBarras.innerHTML = seg.distribucion.map((s, idx) => `
          <div class="seg-barra-item">
            <div class="seg-barra-label">
              <span>${s.nombre} (${s.cantidad} alumnos)</span>
              <span style="font-weight: 700;">${Number(s.porcentaje).toFixed(1)}%</span>
            </div>
            <div class="seg-barra-track">
              <div class="seg-barra-fill" style="width: ${s.porcentaje}%; background: ${coloresSeg[idx % coloresSeg.length]};"></div>
            </div>
          </div>
        `).join("");
      }

      const txtSegDesc = document.getElementById("txt-segmento-desc");
      if (txtSegDesc && seg.descripcion) {
        txtSegDesc.innerHTML = `Segmento predominante: <strong>${seg.segmento_actual}</strong>. ${seg.descripcion}`;
      }

      // 5. Gráfico de Tendencia Semanal (Chart.js)
      const t = data.tendencia_semanal || {};
      const ctxTendencia = document.getElementById("chart-tendencia-semanal")?.getContext("2d");
      if (ctxTendencia) {
        if (chartTendencia) chartTendencia.destroy();
        chartTendencia = new Chart(ctxTendencia, {
          type: "line",
          data: {
            labels: t.labels || ["Lun", "Mar", "Mié", "Jue", "Vie"],
            datasets: [
              {
                label: "Asistencia (%)",
                data: (t.asistencia || []).map(v => Math.round(v * 100)),
                borderColor: "#f97316",
                backgroundColor: "rgba(249,115,22,0.14)",
                tension: 0.35,
                fill: true,
                pointRadius: 4,
                borderWidth: 2
              },
              {
                label: "Clima Emocional + (%)",
                data: (t.emocion_positiva || []).map(v => Math.round(v * 100)),
                borderColor: "#10b981",
                backgroundColor: "rgba(16,185,129,0.08)",
                tension: 0.35,
                fill: true,
                pointRadius: 4,
                borderWidth: 2
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: { min: 0, max: 100, ticks: { callback: v => `${v}%` } }
            }
          }
        });
      }

      // 6. Gráfico EmoScan (Histograma FERPlus)
      const emo = data.emoscan || {};
      const ctxEmo = document.getElementById("chart-emoscan-dist")?.getContext("2d");
      if (ctxEmo && Array.isArray(emo.distribucion)) {
        if (chartEmo) chartEmo.destroy();
        const emoColors = {
          neutral: "#94a3b8",
          happy: "#10b981",
          sad: "#f97316",
          fear: "#8b5cf6",
          surprise: "#f59e0b",
          angry: "#f43f5e"
        };
        chartEmo = new Chart(ctxEmo, {
          type: "bar",
          data: {
            labels: emo.distribucion.map(e => e.key.toUpperCase()),
            datasets: [{
              label: "% de detecciones",
              data: emo.distribucion.map(e => e.pct),
              backgroundColor: emo.distribucion.map(e => emoColors[e.key] || "#2563eb"),
              borderRadius: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              y: { min: 0, max: 60, ticks: { callback: v => `${v}%` } }
            }
          }
        });
      }

      // 7. Tabla de Estadística Descriptiva
      const e = data.estadisticas || {};
      const tbodyStats = document.getElementById("tabla-estadistica-cuerpo");
      if (tbodyStats) {
        const filas = [
          ["Media Clima Emocional (Happy + Neutral)", `${(e.media_emocional_positiva * 100).toFixed(1)}%`, "Promedio de expresiones receptivas en sesiones de clase."],
          ["Mediana de Asistencia", `${(e.mediana_asistencia * 100).toFixed(0)}%`, "Valor central del grupo (robusto frente a valores atípicos)."],
          ["Desviación Estándar de Asistencia", `±${e.desviacion_std_engagement}`, "Dispersión muestral respecto a la media de asistencia."],
          ["Varianza Muestral", `${e.varianza_asistencia}`, "Grado de variabilidad cuadrática en el registro de asistencia."],
          ["Probabilidad Empírica Global P(Asistencia)", `${(e.probabilidad_asistencia_alta * 100).toFixed(1)}%`, "Frecuencia acumulada histórica de asistencias + tardanzas."],
          ["Registros Totales Procesados", Number(e.total_sesiones_analizadas).toLocaleString("es-PE"), "Dataset consolidado de biometría y sesiones de aula."],
          ["Estudiantes en Seguimiento", `${e.total_estudiantes} alumnos`, "Matrícula total vinculada al análisis de IA."]
        ];

        tbodyStats.innerHTML = filas.map(([met, val, desc]) => `
          <tr>
            <td style="font-weight: 600; color: #1e293b;">${met}</td>
            <td style="text-align: right; font-family: monospace; font-weight: 700; color: #2563eb;">${val}</td>
            <td style="color: #64748b; font-size: 0.85rem;">${desc}</td>
          </tr>
        `).join("");
      }

    } catch (err) {
      console.error("Error al cargar el Dashboard de Indicadores ML:", err);
    }
  }

  cargarDashboard();
});

