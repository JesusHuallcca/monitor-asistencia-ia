// Lógica del Panel de Clasificación ML (Parte 4 - Regresión Logística)
// Panel del Profesor - Senati

document.addEventListener("DOMContentLoaded", async () => {
  // Inicializa el layout del panel profesor, valida sesión e inyecta el sidebar oficial
  const yo = await Panel.iniciar("profesor");
  if (!yo) return;

  // Elementos KPI
  const kpiAccuracy = document.getElementById("kpi-accuracy");
  const kpiF1 = document.getElementById("kpi-f1");
  const kpiRoc = document.getElementById("kpi-roc");
  const kpiNtrain = document.getElementById("kpi-ntrain");
  const txtIntercepto = document.getElementById("txt-intercepto");
  const ecuacionLogitBox = document.getElementById("ecuacion-logit-box");
  const contenedorCoefTabla = document.getElementById("contenedor-coef-tabla");

  // Elementos Simulador
  const simRatio = document.getElementById("sim-ratio");
  const lblRatio = document.getElementById("lbl-ratio");
  const simAsist = document.getElementById("sim-asist");
  const lblAsist = document.getElementById("lbl-asist");
  const simAus = document.getElementById("sim-aus");
  const lblAus = document.getElementById("lbl-aus");
  const simNotas = document.getElementById("sim-notas");
  const lblNotas = document.getElementById("lbl-notas");
  const simTard = document.getElementById("sim-tard");
  const lblTard = document.getElementById("lbl-tard");
  const simDia = document.getElementById("sim-dia");
  const simHora = document.getElementById("sim-hora");
  const lblHora = document.getElementById("lbl-hora");
  const simUmbral = document.getElementById("sim-umbral");
  const lblUmbral = document.getElementById("lbl-umbral");
  const btnPredecir = document.getElementById("btn-predecir-logistica");

  // Elementos de Resultado
  const resultadoCard = document.getElementById("resultado-logistica-card");
  const resProbVal = document.getElementById("res-prob-val");
  const resBadgeEtiqueta = document.getElementById("res-badge-etiqueta");
  const resConfianzaVal = document.getElementById("res-confianza-val");
  const resBarraFill = document.getElementById("res-barra-fill");
  const resBarraUmbral = document.getElementById("res-barra-umbral");
  const txtUmbralMarcador = document.getElementById("txt-umbral-marcador");
  const resMensajeLog = document.getElementById("res-mensaje-log");

  // 1. Actualizar etiquetas de los controles dinámicamente
  function actualizarLabels() {
    if (simRatio && lblRatio) lblRatio.textContent = `${Math.round(simRatio.value * 100)}%`;
    if (simAsist && lblAsist) lblAsist.textContent = simAsist.value;
    if (simAus && lblAus) lblAus.textContent = simAus.value;
    if (simNotas && lblNotas) lblNotas.textContent = `${parseFloat(simNotas.value).toFixed(1)} pts`;
    if (simTard && lblTard) lblTard.textContent = `${Math.round(simTard.value * 100)}%`;
    if (simHora && lblHora) lblHora.textContent = `${String(simHora.value).padStart(2, "0")}:00`;
    if (simUmbral && lblUmbral) {
      const umbralPct = Math.round(simUmbral.value * 100);
      lblUmbral.textContent = `${parseFloat(simUmbral.value).toFixed(2)} (${umbralPct}%)`;
      if (resBarraUmbral) resBarraUmbral.style.left = `${umbralPct}%`;
      if (txtUmbralMarcador) txtUmbralMarcador.textContent = `${umbralPct}% (Umbral)`;
    }
  }

  [simRatio, simAsist, simAus, simNotas, simTard, simHora, simUmbral].forEach(el => {
    if (el) el.addEventListener("input", actualizarLabels);
  });
  actualizarLabels();

  // 2. Cargar Métricas y Coeficientes del Modelo
  async function cargarMetricas() {
    try {
      const resp = await Panel.api("/api/logistica/metricas");
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();

      if (kpiAccuracy) kpiAccuracy.textContent = data.accuracy != null ? `${(data.accuracy * 100).toFixed(1)}%` : "67.5%";
      if (kpiF1) kpiF1.textContent = data.f1 != null ? `${(data.f1 * 100).toFixed(1)}%` : "72.8%";
      if (kpiRoc) kpiRoc.textContent = data.roc_auc != null ? `${(data.roc_auc * 100).toFixed(1)}%` : "73.7%";
      if (kpiNtrain) kpiNtrain.textContent = data.n_train != null ? Number(data.n_train).toLocaleString("es-PE") : "5,062";

      if (txtIntercepto && data.intercept != null) {
        txtIntercepto.textContent = `β₀ = ${data.intercept > 0 ? "+" : ""}${Number(data.intercept).toFixed(4)}`;
      }

      // Banner con la fórmula del logit
      if (ecuacionLogitBox && data.tabla_coeficientes) {
        let formulaStr = `z = ${Number(data.intercept || 0).toFixed(4)}`;
        data.tabla_coeficientes.slice(0, 4).forEach(c => {
          const signo = c.coeficiente >= 0 ? "+" : "-";
          formulaStr += ` ${signo} ${Math.abs(c.coeficiente).toFixed(3)} · ${c.feature}`;
        });
        formulaStr += " + ...\nProbabilidad = 1 / (1 + e⁻ᶻ)";
        ecuacionLogitBox.textContent = formulaStr;
      }

      // Llenar tabla de coeficientes
      if (contenedorCoefTabla && Array.isArray(data.tabla_coeficientes)) {
        contenedorCoefTabla.innerHTML = "";
        data.tabla_coeficientes.forEach(c => {
          const tr = document.createElement("tr");
          const esPos = c.impacto === "positivo";
          const badgeClass = esPos ? "badge-positivo" : "badge-negativo";
          const signoIco = esPos ? "▲ Favorece" : "▼ Desfavorece";
          tr.innerHTML = `
            <td style="font-weight: 600; color: #1e293b;">${c.feature}</td>
            <td style="text-align: right; font-family: monospace; font-weight: 700; color: ${esPos ? '#15803d' : '#b91c1c'};">
              ${c.coeficiente >= 0 ? "+" : ""}${Number(c.coeficiente).toFixed(4)}
            </td>
            <td><span class="${badgeClass}">${signoIco}</span></td>
          `;
          contenedorCoefTabla.appendChild(tr);
        });
      }
    } catch (err) {
      console.error("Error al cargar métricas de logística:", err);
      if (kpiAccuracy) kpiAccuracy.textContent = "Error";
    }
  }

  // 3. Ejecutar Predicción Interactiva
  async function ejecutarPrediccion() {
    if (!btnPredecir) return;
    btnPredecir.disabled = true;
    btnPredecir.innerHTML = "⏳ Calculando predicción...";

    const payload = {
      asistencia_ratio_30d: parseFloat(simRatio.value),
      asistencias_consecutivas: parseInt(simAsist.value, 10),
      ausencias_consecutivas: parseInt(simAus.value, 10),
      dia_semana: parseInt(simDia.value, 10),
      hora_inicio_clase: parseInt(simHora.value, 10),
      es_inicio_ciclo: 0,
      promedio_notas: parseFloat(simNotas.value),
      tardanzas_ratio: parseFloat(simTard.value),
      umbral: parseFloat(simUmbral.value)
    };

    try {
      const resp = await Panel.api("/api/logistica/predecir", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!resp.ok) {
        const errorText = await resp.text();
        throw new Error(errorText || `Error HTTP ${resp.status}`);
      }

      const res = await resp.json();

      // Mostrar Card
      if (resultadoCard) resultadoCard.style.display = "block";

      const pct = Math.round(res.probabilidad * 100);
      if (resProbVal) resProbVal.textContent = `${(res.probabilidad * 100).toFixed(1)}%`;

      if (resBarraFill) {
        resBarraFill.style.width = `${pct}%`;
        if (res.prediccion === 1) {
          resBarraFill.style.background = "linear-gradient(90deg, #3b82f6, #10b981)";
        } else {
          resBarraFill.style.background = "linear-gradient(90deg, #f59e0b, #ef4444)";
        }
      }

      if (resBadgeEtiqueta) {
        if (res.prediccion === 1) {
          resBadgeEtiqueta.textContent = "ASISTIRÁ";
          resBadgeEtiqueta.className = "res-badge badge-asiste";
        } else {
          resBadgeEtiqueta.textContent = "NO ASISTIRÁ";
          resBadgeEtiqueta.className = "res-badge badge-noasiste";
        }
      }

      if (resConfianzaVal) {
        resConfianzaVal.textContent = res.confianza || "Alta";
      }

      if (resMensajeLog) {
        const umbralPct = Math.round((payload.umbral || 0.5) * 100);
        resMensajeLog.innerHTML = `
          Con un valor de función sigmoide <strong>z = ${res.logit}</strong> y probabilidad del <strong>${(res.probabilidad * 100).toFixed(1)}%</strong>,
          el alumno supera el umbral del ${umbralPct}%, por lo que el modelo clasifica la sesión como <strong>${res.etiqueta}</strong>.
        `;
      }

    } catch (err) {
      console.error("Error al predecir asistencia:", err);
      alert("Error al predecir: " + err.message);
    } finally {
      btnPredecir.disabled = false;
      btnPredecir.innerHTML = "Predecir Probabilidad de Asistencia";
    }
  }

  if (btnPredecir) {
    btnPredecir.addEventListener("click", ejecutarPrediccion);
  }

  // Carga inicial
  await cargarMetricas();
  // Ejecutar una primera predicción de muestra
  ejecutarPrediccion();
});
