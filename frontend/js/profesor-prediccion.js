// Lógica del Simulador de Predicción ML (Parte 2 - Regresión Lineal)
// Panel del Profesor

document.addEventListener("DOMContentLoaded", async () => {
  const yo = await Panel.iniciar("profesor");
  if (!yo) return;

  // Elementos KPI
  const kpiR2Multiple = document.getElementById("kpi-r2-multiple");
  const kpiMaeMultiple = document.getElementById("kpi-mae-multiple");
  const kpiR2Simple = document.getElementById("kpi-r2-simple");
  const kpiFactorTop = document.getElementById("kpi-factor-top");
  const formulaBox = document.getElementById("ecuacion-modelo-box");
  const contenedorFeatures = document.getElementById("contenedor-features-tabla");

  // Elementos Gráfico
  const imgGrafico = document.getElementById("img-grafico-regresion");
  const tabsGraficos = document.querySelectorAll(".btn-tab-grafico");

  // Elementos Simulador
  const formSimulador = document.getElementById("form-simulador-ml");
  const btnPredecir = document.getElementById("btn-predecir-ml");
  const inputDia = document.getElementById("sim-dia");
  const inputHora = document.getElementById("sim-hora");
  const inputConfianza = document.getElementById("sim-confianza");
  const lblConfianza = document.getElementById("lbl-sim-confianza");
  const inputLiveness = document.getElementById("sim-liveness");
  const lblLiveness = document.getElementById("lbl-sim-liveness");

  // Sliders de emociones
  const sliderHappy = document.getElementById("sim-happy");
  const sliderNeutral = document.getElementById("sim-neutral");
  const sliderSad = document.getElementById("sim-sad");
  const sliderAngry = document.getElementById("sim-angry");
  const lblHappy = document.getElementById("lbl-sim-happy");
  const lblNeutral = document.getElementById("lbl-sim-neutral");
  const lblSad = document.getElementById("lbl-sim-sad");
  const lblAngry = document.getElementById("lbl-sim-angry");

  // Elementos de Resultado
  const resultadoCard = document.getElementById("resultado-prediccion-card");
  const resPuntajeNum = document.getElementById("res-puntaje-num");
  const resPuntajeBarra = document.getElementById("res-puntaje-barra");
  const resBadgeEstado = document.getElementById("res-badge-estado");
  const resMensaje = document.getElementById("res-interpretacion-msg");
  const resHoraNorm = document.getElementById("res-hora-norm");
  const resConfNorm = document.getElementById("res-conf-norm");

  // Actualizar labels de sliders dinámicamente
  function actualizarLabelsSliders() {
    if (lblConfianza && inputConfianza) lblConfianza.textContent = `${inputConfianza.value}%`;
    if (lblLiveness && inputLiveness) lblLiveness.textContent = `${inputLiveness.value}%`;
    if (lblHappy && sliderHappy) lblHappy.textContent = `${sliderHappy.value}%`;
    if (lblNeutral && sliderNeutral) lblNeutral.textContent = `${sliderNeutral.value}%`;
    if (lblSad && sliderSad) lblSad.textContent = `${sliderSad.value}%`;
    if (lblAngry && sliderAngry) lblAngry.textContent = `${sliderAngry.value}%`;
  }

  [inputConfianza, inputLiveness, sliderHappy, sliderNeutral, sliderSad, sliderAngry].forEach(el => {
    if (el) el.addEventListener("input", actualizarLabelsSliders);
  });
  actualizarLabelsSliders();

  // 1. Cargar Métricas y Coeficientes
  async function cargarMetricas() {
    try {
      const resp = await Panel.api("/api/regresion/metricas");
      if (!resp.ok) {
        Panel.avisar("No se pudieron cargar las métricas de la regresión lineal.", "error");
        return;
      }
      const data = await resp.json();

      if (kpiR2Multiple) kpiR2Multiple.textContent = `${(data.r2_multiple * 100).toFixed(1)}%`;
      if (kpiMaeMultiple) kpiMaeMultiple.textContent = `±${data.mae_multiple.toFixed(2)} pts`;
      if (kpiR2Simple) kpiR2Simple.textContent = `${(data.r2_simple * 100).toFixed(1)}%`;
      if (kpiFactorTop) kpiFactorTop.textContent = "Hora de llegada (-11.59)";

      if (formulaBox && data.ecuacion_resumen) {
        formulaBox.textContent = data.ecuacion_resumen;
      }

      // Renderizar tabla de coeficientes
      if (contenedorFeatures && data.features) {
        contenedorFeatures.replaceChildren();
        data.features.forEach(f => {
          const tr = document.createElement("tr");
          const esNegativo = f.coeficiente < 0;
          const colorCoef = esNegativo ? "#dc2626" : "#16a34a";
          const signo = f.coeficiente > 0 ? "+" : "";

          let badgeClass = "badge-neutral";
          if (f.impacto.includes("Positivo")) badgeClass = "badge-positivo";
          else if (f.impacto.includes("Negativo") || f.impacto.includes("Alto")) badgeClass = "badge-negativo";

          tr.innerHTML = `
            <td><code>${f.feature}</code></td>
            <td><strong style="color: ${colorCoef};">${signo}${f.coeficiente.toFixed(4)}</strong></td>
            <td><span class="impacto-tag ${badgeClass}">${f.impacto}</span></td>
            <td style="color: #64748b; font-size: 0.85rem;">${f.descripcion}</td>
          `;
          contenedorFeatures.appendChild(tr);
        });
      }
    } catch (e) {
      console.error("Error al cargar métricas:", e);
    }
  }

  // 2. Cargar Gráficos con Cache Buster y Blob
  async function cargarGrafico(nombreArchivo) {
    if (!imgGrafico) return;
    try {
      imgGrafico.style.opacity = "0.4";
      const resp = await Panel.api(`/api/regresion/grafico/${nombreArchivo}?t=${Date.now()}`);
      if (resp.ok) {
        const blob = await resp.blob();
        imgGrafico.src = URL.createObjectURL(blob);
        imgGrafico.style.display = "block";
      }
    } catch (e) {
      console.error("Error al cargar gráfico:", e);
    } finally {
      imgGrafico.style.opacity = "1";
    }
  }

  // Pestañas de gráficos
  tabsGraficos.forEach(tab => {
    tab.addEventListener("click", () => {
      tabsGraficos.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const tipo = tab.dataset.grafico || "prediccion_vs_real.png";
      cargarGrafico(tipo);
    });
  });

  // 3. Ejecutar Predicción Interactiva (con Debounce/Anti-Spam)
  if (btnPredecir) {
    btnPredecir.addEventListener("click", async (e) => {
      e.preventDefault();
      btnPredecir.disabled = true;
      btnPredecir.innerHTML = `<span>⏳ Calculando inferencia...</span>`;

      const payload = {
        dia_semana: parseInt(inputDia?.value || "1", 10),
        hora_llegada: inputHora?.value || "08:05",
        confianza: parseFloat(inputConfianza?.value || "90"),
        liveness_score: parseFloat(inputLiveness?.value || "88"),
        happy: parseFloat(sliderHappy?.value || "40"),
        neutral: parseFloat(sliderNeutral?.value || "35"),
        sad: parseFloat(sliderSad?.value || "15"),
        angry: parseFloat(sliderAngry?.value || "10")
      };

      try {
        const resp = await Panel.api("/api/regresion/predecir", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (!resp.ok) {
          const err = await resp.json();
          Panel.avisar(err.detail || "Error al calcular la predicción.", "error");
          return;
        }

        const res = await resp.json();

        // Actualizar visualización del resultado
        if (resultadoCard) resultadoCard.style.display = "block";
        if (resPuntajeNum) resPuntajeNum.textContent = `${res.puntaje.toFixed(1)}`;
        if (resPuntajeBarra) {
          resPuntajeBarra.style.width = `${Math.min(100, Math.max(0, res.puntaje))}%`;
          resPuntajeBarra.style.backgroundColor = res.color || "#2563eb";
        }
        if (resBadgeEstado) {
          resBadgeEstado.textContent = res.estado;
          resBadgeEstado.style.backgroundColor = `${res.color}22`;
          resBadgeEstado.style.color = res.color;
          resBadgeEstado.style.borderColor = res.color;
        }
        if (resMensaje) resMensaje.textContent = res.interpretacion;
        if (resHoraNorm && res.datos_normalizados) {
          resHoraNorm.textContent = `${res.datos_normalizados.hora_legible} (${res.datos_normalizados.hora_llegada_minutos} min)`;
        }
        if (resConfNorm && res.datos_normalizados) {
          resConfNorm.textContent = `${res.datos_normalizados.confianza_pct}% facial / ${res.datos_normalizados.liveness_pct}% liveness`;
        }

        Panel.avisar(`Predicción calculada: ${res.estado} (${res.puntaje} pts)`, "exito");

      } catch (err) {
        console.error("Error al predecir:", err);
        Panel.avisar("No se pudo conectar con el servidor predictivo.", "error");
      } finally {
        btnPredecir.disabled = false;
        btnPredecir.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          Calcular Predicción en Vivo
        `;
      }
    });
  }

  // Inicialización
  await cargarMetricas();
  await cargarGrafico("prediccion_vs_real.png");
});

