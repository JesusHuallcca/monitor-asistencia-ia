// Detector facial en el navegador: puntos en vivo + retos de vida.
// Usa MediaPipe Face Landmarker (red neuronal de Google que corre en tu navegador).
const RostroVivo = (() => {
  const URL_JS =
    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision/vision_bundle.mjs";
  const URL_WASM =
    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm";
  const URL_MODELO =
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";

  // ---- Ajustes (se calibran con tu cámara; pon DEPURAR = true para ver los valores) ----
  const DEPURAR = false;
  const UMBRAL_GIRO = 0.12; // cuánto debe girar la cabeza
  const UMBRAL_FRENTE = 0.06; // tolerancia para considerar que miras al frente
  const INVERTIR_GIRO = false; // pon true si "izquierda" y "derecha" te salen al revés
  const OJO_CERRADO = 0.5;
  const OJO_ABIERTO = 0.3;
  const ESPERA_FRENTE = 700; // ms quieto y de frente antes de capturar
  const LIMITE_PASO = 25000; // ms máximos por paso
  const VERDE = "#22c55e";
  const ROJO = "#ef4444";

  const TEXTOS = {
    frente: "Mira al frente y no te muevas.",
    parpadeo: "Parpadea una vez.",
    giro_izq: "Gira lentamente la cabeza hacia tu izquierda.",
    giro_der: "Gira lentamente la cabeza hacia tu derecha.",
  };

  let modulo = null;
  let landmarker = null;
  let indices = [];
  let video = null;
  let canvas = null;
  let ctx = null;
  let activo = false;
  let raf = 0;
  let errorMostrado = false;
  let brillo = 128;
  let contador = 0;
  let f = {
    hayRostro: false,
    ok: false,
    guia: "",
    lm: null,
    yaw: 0,
    cierre: 0,
    caja: null,
  };
  let P = null; // paso en curso

  const lienzoBrillo = document.createElement("canvas");
  lienzoBrillo.width = 32;
  lienzoBrillo.height = 24;

  // ---------- Carga del modelo ----------
  function calcularIndices() {
    const FL = modulo.FaceLandmarker;
    const grupos = [
      FL.FACE_LANDMARKS_FACE_OVAL,
      FL.FACE_LANDMARKS_LEFT_EYE,
      FL.FACE_LANDMARKS_RIGHT_EYE,
      FL.FACE_LANDMARKS_LEFT_EYEBROW,
      FL.FACE_LANDMARKS_RIGHT_EYEBROW,
      FL.FACE_LANDMARKS_LIPS,
    ].filter(Boolean);
    const set = new Set();
    for (const g of grupos)
      for (const c of g) {
        set.add(c.start);
        set.add(c.end);
      }
    [1, 2, 4, 5, 6, 168, 195, 197].forEach((i) => set.add(i)); // nariz
    if (set.size < 40) for (let i = 0; i < 478; i += 5) set.add(i);
    return [...set];
  }

  async function cargar(alProgreso) {
    if (landmarker) return;
    if (alProgreso) alProgreso("Cargando el detector facial…");
    try {
      modulo = await import(URL_JS);
      const vision = await modulo.FilesetResolver.forVisionTasks(URL_WASM);
      const opciones = (delegate) => ({
        baseOptions: { modelAssetPath: URL_MODELO, delegate },
        runningMode: "VIDEO",
        numFaces: 2,
        outputFaceBlendshapes: true,
      });
      try {
        landmarker = await modulo.FaceLandmarker.createFromOptions(
          vision,
          opciones("GPU"),
        );
      } catch (e) {
        landmarker = await modulo.FaceLandmarker.createFromOptions(
          vision,
          opciones("CPU"),
        );
      }
      indices = calcularIndices();
    } catch (e) {
      console.error(e);
      throw new Error(
        "No se pudo cargar el detector facial. Revisa tu conexión a internet.",
      );
    }
  }

  // ---------- Cámara y bucle ----------
  async function iniciar(videoEl) {
    await cargar();
    await Camara.iniciar(videoEl);
    video = videoEl;
    canvas = video.parentElement.querySelector("canvas.capa-puntos");
    if (!canvas) {
      canvas = document.createElement("canvas");
      canvas.className = "capa-puntos";
      video.after(canvas);
    }
    ctx = canvas.getContext("2d");
    activo = true;
    errorMostrado = false;
    f = {
      hayRostro: false,
      ok: false,
      guia: "No veo tu rostro. Mira a la cámara.",
      lm: null,
      yaw: 0,
      cierre: 0,
      caja: null,
    };
    raf = requestAnimationFrame(bucle);
  }

  function detener(videoEl) {
    activo = false;
    cancelAnimationFrame(raf);
    terminar(new Error("cancelado"));
    if (ctx && canvas) ctx.clearRect(0, 0, canvas.width, canvas.height);
    Camara.detener(videoEl || video);
  }

  function bucle() {
    if (!activo) return;
    try {
      if (video.readyState >= 2 && video.videoWidth) {
        const t = performance.now();
        if (contador++ % 12 === 0) medirBrillo();
        procesar(landmarker.detectForVideo(video, t));
        dibujar(t);
        avanzar(t);
      }
    } catch (e) {
      if (!errorMostrado) {
        console.error(e);
        errorMostrado = true;
      }
    }
    raf = requestAnimationFrame(bucle);
  }

  function medirBrillo() {
    const c = lienzoBrillo.getContext("2d", { willReadFrequently: true });
    c.drawImage(video, 0, 0, 32, 24);
    const d = c.getImageData(0, 0, 32, 24).data;
    let suma = 0;
    for (let i = 0; i < d.length; i += 4)
      suma += 0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2];
    brillo = suma / (d.length / 4);
  }

  // ---------- Medidas del rostro ----------
  function procesar(res) {
    const caras = res.faceLandmarks || [];
    if (caras.length === 0) {
      f = {
        hayRostro: false,
        ok: false,
        guia: "No veo tu rostro. Mira a la cámara.",
        lm: null,
        yaw: 0,
        cierre: 0,
        caja: null,
      };
      return;
    }
    const lm = caras[0];
    let minX = 1,
      maxX = 0,
      minY = 1,
      maxY = 0;
    for (const p of lm) {
      if (p.x < minX) minX = p.x;
      if (p.x > maxX) maxX = p.x;
      if (p.y < minY) minY = p.y;
      if (p.y > maxY) maxY = p.y;
    }
    const ancho = maxX - minX;
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;

    // Giro: posición de la nariz respecto al centro de las mejillas (imagen SIN espejo).
    // yaw > 0 = nariz hacia la derecha de la imagen = giraste hacia TU izquierda.
    const izq = Math.min(lm[234].x, lm[454].x);
    const der = Math.max(lm[234].x, lm[454].x);
    const yaw = (lm[1].x - (izq + der) / 2) / Math.max(der - izq, 0.001);

    const bs =
      res.faceBlendshapes && res.faceBlendshapes[0]
        ? res.faceBlendshapes[0].categories
        : [];
    const puntaje = (n) => {
      const c = bs.find((x) => x.categoryName === n);
      return c ? c.score : 0;
    };
    const cierre = Math.min(puntaje("eyeBlinkLeft"), puntaje("eyeBlinkRight"));

    let guia = "";
    if (caras.length > 1) guia = "Debe aparecer una sola persona.";
    else if (ancho < 0.22) guia = "Acércate un poco.";
    else if (ancho > 0.6) guia = "Aléjate un poco.";
    else if (Math.abs(cx - 0.5) > 0.17 || Math.abs(cy - 0.5) > 0.2)
      guia = "Centra tu rostro en la imagen.";
    else if (brillo < 55) guia = "Necesitas más luz en tu rostro.";

    f = {
      hayRostro: true,
      ok: guia === "",
      guia,
      lm,
      yaw,
      cierre,
      caja: { minX, maxX, minY, maxY },
    };
  }

  // ---------- Dibujo de puntos ----------
  function dibujar(t) {
    const w = video.videoWidth;
    const h = video.videoHeight;
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
    ctx.clearRect(0, 0, w, h);
    if (!f.lm) return;

    const bien = f.ok || (P && P.fase === "accion" && f.hayRostro);
    const color = bien ? VERDE : ROJO;

    ctx.fillStyle = color;
    for (const i of indices) {
      const p = f.lm[i];
      ctx.beginPath();
      ctx.arc(p.x * w, p.y * h, 2.2, 0, Math.PI * 2);
      ctx.fill();
    }

    // Esquinas alrededor del rostro
    const pad = 0.03;
    const x0 = (f.caja.minX - pad) * w;
    const x1 = (f.caja.maxX + pad) * w;
    const y0 = (f.caja.minY - pad) * h;
    const y1 = (f.caja.maxY + pad) * h;
    const L = Math.min(x1 - x0, y1 - y0) * 0.18;
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(x0, y0 + L);
    ctx.lineTo(x0, y0);
    ctx.lineTo(x0 + L, y0);
    ctx.moveTo(x1 - L, y0);
    ctx.lineTo(x1, y0);
    ctx.lineTo(x1, y0 + L);
    ctx.moveTo(x1, y1 - L);
    ctx.lineTo(x1, y1);
    ctx.lineTo(x1 - L, y1);
    ctx.moveTo(x0 + L, y1);
    ctx.lineTo(x0, y1);
    ctx.lineTo(x0, y1 - L);
    ctx.stroke();

    // Línea de escaneo mientras el rostro está bien ubicado
    if (bien) {
      const k = (t % 1400) / 1400;
      ctx.fillStyle = "rgba(34, 197, 94, 0.55)";
      ctx.fillRect(x0, y0 + k * (y1 - y0) - 1.5, x1 - x0, 3);
    }
  }

  // ---------- Retos ----------
  const capturar = () => Camara.capturar(video);

  function emitir(texto, tipo) {
    if (!P) return;
    const prefijo =
      P.pasos.length > 1 ? `Paso ${P.i + 1} de ${P.pasos.length} · ` : "";
    const extra = DEPURAR
      ? ` · giro ${f.yaw.toFixed(2)} · ojos ${f.cierre.toFixed(2)} · luz ${Math.round(brillo)}`
      : "";
    const completo = prefijo + texto + extra;
    if (DEPURAR || completo !== P.ultimo) {
      P.ultimo = completo;
      P.alEstado({
        texto: completo,
        tipo,
        paso: P.i + 1,
        total: P.pasos.length,
      });
    }
  }

  function iniciarPaso(t, anterior) {
    const def = P.pasos[P.i];
    P.fase = def.accion === "frente" ? "frente" : "accion";
    P.tInicio = t;
    P.pausa = anterior ? t + 800 : t;
    P.tHold = null;
    P.cerro = false;
    P.pico = null;
    P.ultimo = null;
    if (anterior) emitir("Paso completado. Prepárate para el siguiente.", "ok");
  }

  function terminar(err) {
    const actual = P;
    P = null;
    if (!actual) return;
    if (err) actual.rechazar(err);
    else actual.resolver(actual.resultados);
  }

  function avanzar(t) {
    if (!P || t < P.pausa) return;
    const def = P.pasos[P.i];

    if (t - P.tInicio > LIMITE_PASO) {
      terminar(new Error("No se completó el paso a tiempo. Intenta de nuevo."));
      return;
    }

    // Fase 1: realizar la acción (parpadear o girar)
    if (P.fase === "accion") {
      if (!f.hayRostro) {
        emitir(f.guia, "error");
        return;
      }
      let hecho = false;
      let texto;
      if (def.accion === "parpadeo") {
        texto = TEXTOS.parpadeo;
        if (f.cierre > OJO_CERRADO) P.cerro = true;
        else if (P.cerro && f.cierre < OJO_ABIERTO) hecho = true;
      } else {
        texto = TEXTOS["giro_" + def.dir];
        const signo = (def.dir === "izq" ? 1 : -1) * (INVERTIR_GIRO ? -1 : 1);
        if (f.yaw * signo >= UMBRAL_GIRO) {
          hecho = true;
          P.pico = capturar();
        }
      }
      emitir(texto, "");
      if (hecho) {
        P.fase = "frente";
        P.tHold = null;
        emitir("Muy bien. Vuelve a mirar al frente.", "ok");
      }
      return;
    }

    // Fase 2: de frente, quieto y bien ubicado
    if (!f.hayRostro) {
      P.tHold = null;
      emitir(f.guia, "error");
      return;
    }
    const quieto = Math.abs(f.yaw) <= UMBRAL_FRENTE && f.cierre < OJO_ABIERTO;
    if (!f.ok || !quieto) {
      P.tHold = null;
      emitir(
        f.ok
          ? def.accion === "frente"
            ? TEXTOS.frente
            : "Vuelve a mirar al frente."
          : f.guia,
        f.ok ? "" : "error",
      );
      return;
    }
    if (P.tHold === null) P.tHold = t;
    emitir("Mantén la posición…", "ok");
    if (t - P.tHold < ESPERA_FRENTE) return;

    P.resultados.push({
      accion: def.accion,
      dir: def.dir || null,
      pico: P.pico,
      frente: capturar(),
    });
    P.i++;
    if (P.i >= P.pasos.length) {
      terminar(null);
      return;
    }
    iniciarPaso(t, true);
  }

  // pasos: [{accion:"frente"}, {accion:"parpadeo"}, {accion:"giro", dir:"izq"|"der"}]
  // Devuelve [{accion, dir, pico, frente}] con los fotogramas capturados.
  function ejecutar(pasos, alEstado) {
    return new Promise((resolver, rechazar) => {
      if (!activo) {
        rechazar(new Error("La cámara no está activa."));
        return;
      }
      if (P) {
        rechazar(new Error("Ya hay una verificación en curso."));
        return;
      }
      P = { pasos, i: 0, alEstado, resolver, rechazar, resultados: [] };
      iniciarPaso(performance.now(), false);
    });
  }

  function accionAleatoria() {
    const opciones = [
      { accion: "parpadeo" },
      { accion: "giro", dir: "izq" },
      { accion: "giro", dir: "der" },
    ];
    const n = new Uint32Array(1);
    crypto.getRandomValues(n);
    return opciones[n[0] % opciones.length];
  }

  return { cargar, iniciar, detener, ejecutar, accionAleatoria };
})();
