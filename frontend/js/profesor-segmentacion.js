// Lógica para la visualización de Segmentación IA (Parte 3 - K-Means)
// Panel del Profesor

document.addEventListener("DOMContentLoaded", async () => {
  const yo = await Panel.iniciar("profesor");
  if (!yo) return;

  // Elementos KPI
  const kpiK = document.getElementById("kpi-seg-k");
  const kpiSilueta = document.getElementById("kpi-seg-silueta");
  const kpiInercia = document.getElementById("kpi-seg-inercia");
  const kpiPca = document.getElementById("kpi-seg-pca");

  // Contenedores
  const contenedorClusters = document.getElementById("contenedor-tarjetas-clusters");
  const contenedorTablaK = document.getElementById("contenedor-evaluacion-k-tabla");
  const imgGrafico = document.getElementById("img-grafico-segmentacion");
  const btnDescargarCsv = document.getElementById("btn-descargar-segmentos-csv");

  // Pestañas de Vista (Reporte vs Laboratorio)
  const btnTabReporte = document.getElementById("tab-btn-reporte");
  const btnTabLab = document.getElementById("tab-btn-laboratorio");
  const secReporte = document.getElementById("sec-reporte-oficial");
  const secLab = document.getElementById("sec-laboratorio-interactivo");

  if (btnTabReporte && btnTabLab && secReporte && secLab) {
    btnTabReporte.addEventListener("click", () => {
      btnTabReporte.classList.add("active");
      btnTabLab.classList.remove("active");
      secReporte.style.display = "block";
      secLab.style.display = "none";
    });

    btnTabLab.addEventListener("click", () => {
      btnTabLab.classList.add("active");
      btnTabReporte.classList.remove("active");
      secReporte.style.display = "none";
      secLab.style.display = "block";
      // Si Plotly necesita redibujarse al hacerse visible
      window.dispatchEvent(new Event("resize"));
    });
  }

  // 1. Cargar Métricas Oficiales
  async function cargarMetricas() {
    try {
      const resp = await Panel.api("/api/segmentacion/metricas");
      if (!resp.ok) {
        Panel.avisar("No se pudieron cargar las métricas de segmentación.", "error");
        return;
      }
      const data = await resp.json();

      if (kpiK) kpiK.textContent = `K = ${data.k_elegido}`;
      if (kpiSilueta) kpiSilueta.textContent = data.silueta?.toFixed(4) || "0.2953";
      if (kpiInercia) kpiInercia.textContent = data.inercia?.toFixed(1) || "194.4";
      if (kpiPca) kpiPca.textContent = `${data.varianza_pca?.total_explicada_pct || 88.3}%`;

      // Tabla de evaluación de K (Método del codo y silueta)
      if (contenedorTablaK && data.evaluacion_k) {
        contenedorTablaK.replaceChildren();
        data.evaluacion_k.forEach(row => {
          const tr = document.createElement("tr");
          const esSel = row.es_seleccionado;
          if (esSel) tr.style.backgroundColor = "#eff6ff";

          tr.innerHTML = `
            <td>
              <strong>K = ${row.k}</strong>
              ${esSel ? '<span style="margin-left:6px; font-size:10px; background:#2563eb; color:#fff; padding:2px 6px; border-radius:4px; font-weight:700;">ELEGIDO</span>' : ''}
            </td>
            <td><strong style="color: ${esSel ? '#2563eb' : '#0f172a'};">${row.silueta.toFixed(4)}</strong></td>
            <td>${row.inercia.toFixed(2)}</td>
            <td>
              <div style="width: 100%; height: 6px; background-color: #e2e8f0; border-radius: 99px; overflow: hidden;">
                <div style="width: ${Math.min(100, Math.max(10, row.silueta * 250))}%; height: 100%; background-color: ${esSel ? '#2563eb' : '#94a3b8'}; border-radius: 99px;"></div>
              </div>
            </td>
          `;
          contenedorTablaK.appendChild(tr);
        });
      }

    } catch (e) {
      console.error("Error al cargar métricas de segmentación:", e);
    }
  }

  // 2. Cargar Resumen de los 3 Clusters (S1, S2, S3)
  async function cargarClusters() {
    try {
      const resp = await Panel.api("/api/segmentacion/clusters");
      if (!resp.ok) return;
      const data = await resp.json();

      if (contenedorClusters && data.segmentos) {
        contenedorClusters.replaceChildren();
        data.segmentos.forEach(seg => {
          const card = document.createElement("div");
          card.className = "seg-cluster-summary-card";
          card.style.borderLeft = `5px solid ${seg.color}`;

          card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
              <div>
                <span style="font-size:11px; font-weight:800; color:${seg.color}; text-transform:uppercase; letter-spacing:0.04em;">
                  GRUPO ${seg.id}
                </span>
                <h3 style="margin:2px 0 0; font-size:1.05rem; font-weight:700; color:#0f172a;">${seg.nombre}</h3>
              </div>
              <span class="seg-risk-tag" style="background:${seg.color}15; color:${seg.color}; border:1px solid ${seg.color}40; padding:3px 8px; border-radius:6px; font-size:11px; font-weight:700;">
                Riesgo ${seg.nivel_riesgo}
              </span>
            </div>

            <p style="margin:0 0 12px; font-size:0.8rem; color:#64748b; line-height:1.4;">${seg.perfil_resumen}</p>

            <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; background:#f8fafc; border-radius:8px; padding:10px; margin-bottom:12px; text-align:center;">
              <div>
                <span style="display:block; font-size:11px; color:#64748b;">Estudiantes</span>
                <strong style="font-size:1.05rem; color:#0f172a;">${seg.n_estudiantes} <small style="font-size:10px; color:#64748b;">(${seg.porcentaje}%)</small></strong>
              </div>
              <div>
                <span style="display:block; font-size:11px; color:#64748b;">Asistencia</span>
                <strong style="font-size:1.05rem; color:${seg.color};">${seg.asistencia_media_pct}%</strong>
              </div>
              <div>
                <span style="display:block; font-size:11px; color:#64748b;">Nota Media</span>
                <strong style="font-size:1.05rem; color:#0f172a;">${seg.nota_media}</strong>
              </div>
            </div>

            <div style="font-size:0.8rem; color:#334155; border-top:1px solid #f1f5f9; padding-top:8px;">
              <strong style="color:#0f172a;">Acción Pedagógica:</strong> ${seg.recomendacion}
            </div>
          `;
          contenedorClusters.appendChild(card);
        });
      }
    } catch (e) {
      console.error("Error al cargar resumen de clusters:", e);
    }
  }

  // 3. Cargar Gráfico Multicuadrante Canónico
  async function cargarGrafico() {
    if (!imgGrafico) return;
    try {
      const resp = await Panel.api("/api/segmentacion/grafico/visualizacion_clusters.png");
      if (resp.ok) {
        const blob = await resp.blob();
        imgGrafico.src = URL.createObjectURL(blob);
        imgGrafico.style.display = "block";
      }
    } catch (e) {
      console.error("Error al cargar gráfico de clusters:", e);
    }
  }

  // 4. Descargar CSV con token de autenticación
  if (btnDescargarCsv) {
    btnDescargarCsv.addEventListener("click", async () => {
      try {
        btnDescargarCsv.disabled = true;
        btnDescargarCsv.textContent = "⏳ Preparando descarga...";
        const resp = await Panel.api("/api/segmentacion/descargar-csv");
        if (resp.ok) {
          const blob = await resp.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = "segmentos_asignados_kmeans.csv";
          document.body.appendChild(a);
          a.click();
          a.remove();
          Panel.avisar("Descarga de segmentos iniciada exitosamente.", "exito");
        } else {
          Panel.avisar("No se pudo descargar el archivo CSV.", "error");
        }
      } catch (err) {
        console.error("Error en descarga:", err);
      } finally {
        btnDescargarCsv.disabled = false;
        btnDescargarCsv.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Descargar Segmentos Asignados (CSV)
        `;
      }
    });
  }

  // Inicializar vista
  await cargarMetricas();
  await cargarClusters();
  await cargarGrafico();
});

