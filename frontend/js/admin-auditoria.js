document.addEventListener("DOMContentLoaded", async () => {
  const yo = await Admin.iniciar();
  if (!yo) return;
  const el = Admin.el.bind(Admin);

  const cuerpo = document.getElementById("tabla-cuerpo");
  const filtroQ = document.getElementById("filtro-q");
  const filtroAccion = document.getElementById("filtro-accion");
  const filtroResultado = document.getElementById("filtro-resultado");
  const filtroDesde = document.getElementById("filtro-desde");
  const filtroHasta = document.getElementById("filtro-hasta");
  const btnMas = document.getElementById("btn-mas");
  const conteo = document.getElementById("conteo");
  const LIMITE = 50;
  let offset = 0;
  let cargados = [];
  let temporizador = null;
  let version = 0;

  const hoy = () => {
    const d = new Date();
    return (
      d.getFullYear() +
      "-" +
      String(d.getMonth() + 1).padStart(2, "0") +
      "-" +
      String(d.getDate()).padStart(2, "0")
    );
  };

  // ---------- Resumen de hoy ----------
  async function cargarResumen() {
    const r = await Admin.api("/api/admin/auditoria/resumen");
    if (!r.ok) return;
    const s = await r.json();
    document.getElementById("st-total").textContent = s.total;
    document.getElementById("st-ingresos").textContent = s.ingresos;
    document.getElementById("st-fallidos").textContent = s.fallidos;
    document.getElementById("st-bloqueos").textContent = s.bloqueos;
  }

  async function cargarAcciones() {
    const r = await Admin.api("/api/admin/auditoria/acciones");
    if (!r.ok) return;
    for (const a of await r.json()) {
      const o = el("option", "", Admin.etiquetaAccion(a));
      o.value = a;
      filtroAccion.appendChild(o);
    }
  }

  // ---------- Tabla ----------
  function filaEvento(e) {
    const tr = el("tr");
    tr.appendChild(el("td", "col-fecha", Admin.fecha(e.fecha)));
    tr.appendChild(el("td", "", e.username ? "@" + e.username : "—"));

    const tdAccion = el("td");
    tdAccion.appendChild(el("span", "badge", Admin.etiquetaAccion(e.accion)));
    tr.appendChild(tdAccion);

    const tdDetalle = el("td", "col-detalle", e.detalle || "");
    tdDetalle.title = e.detalle || "";
    tr.appendChild(tdDetalle);

    tr.appendChild(el("td", "col-ip", e.ip || "—"));

    const tdRes = el("td");
    tdRes.appendChild(
      el(
        "span",
        "estado " + (e.exito ? "activo" : "fallo"),
        e.exito ? "Correcto" : "Fallido",
      ),
    );
    tr.appendChild(tdRes);
    return tr;
  }

  function parametros() {
    const p = new URLSearchParams({
      limit: String(LIMITE),
      offset: String(offset),
    });
    if (filtroQ.value.trim()) p.set("q", filtroQ.value.trim());
    if (filtroAccion.value) p.set("accion", filtroAccion.value);
    if (filtroResultado.value) p.set("exito", filtroResultado.value);
    if (filtroDesde.value) p.set("desde", filtroDesde.value);
    if (filtroHasta.value) p.set("hasta", filtroHasta.value);
    return p;
  }

  async function cargar(reiniciar = true) {
    const mia = ++version;
    if (reiniciar) {
      offset = 0;
      cargados = [];
    }
    btnMas.disabled = true;

    const r = await Admin.api(
      "/api/admin/auditoria?" + parametros().toString(),
    );
    if (mia !== version) return; // llegó una búsqueda más nueva
    if (!r.ok) {
      Admin.avisar(
        await Admin.detalle(r, "No se pudo cargar la auditoría."),
        "error",
      );
      btnMas.disabled = false;
      return;
    }

    const lote = await r.json();
    if (mia !== version) return;
    cargados = cargados.concat(lote);

    if (reiniciar) cuerpo.replaceChildren();
    if (cargados.length === 0) {
      const tr = el("tr");
      const td = el("td", "vacio", "No hay eventos con ese filtro.");
      td.colSpan = 6;
      tr.appendChild(td);
      cuerpo.appendChild(tr);
    } else {
      lote.forEach((e) => cuerpo.appendChild(filaEvento(e)));
    }

    conteo.textContent =
      cargados.length +
      (cargados.length === 1 ? " evento" : " eventos") +
      " mostrados";
    btnMas.hidden = lote.length < LIMITE;
    btnMas.disabled = false;
  }

  btnMas.addEventListener("click", () => {
    offset += LIMITE;
    cargar(false);
  });

  [filtroAccion, filtroResultado, filtroDesde, filtroHasta].forEach((c) =>
    c.addEventListener("change", () => cargar()),
  );
  filtroQ.addEventListener("input", () => {
    clearTimeout(temporizador);
    temporizador = setTimeout(() => cargar(), 300);
  });

  document.getElementById("btn-limpiar").addEventListener("click", () => {
    filtroQ.value = "";
    filtroAccion.value = "";
    filtroResultado.value = "";
    filtroDesde.value = "";
    filtroHasta.value = "";
    cargar();
  });

  // Las tarjetas son atajos de filtro (sobre el día de hoy)
  document.querySelectorAll(".stat").forEach((t) => {
    t.addEventListener("click", () => {
      filtroQ.value = "";
      filtroAccion.value = "";
      filtroResultado.value = "";
      filtroDesde.value = hoy();
      filtroHasta.value = hoy();
      const f = t.dataset.filtro;
      if (f === "ingresos") filtroAccion.value = "login_ok";
      if (f === "fallidos") filtroResultado.value = "false";
      if (f === "bloqueos") filtroAccion.value = "login_bloqueado";
      cargar();
    });
  });

  // ---------- Exportar CSV (solo lo cargado en pantalla) ----------
  function celdaCsv(v) {
    let s = v === null || v === undefined ? "" : String(v);
    if (/^[=+\-@\t\r]/.test(s)) s = "'" + s; // evita que Excel lo trate como fórmula
    return '"' + s.replace(/"/g, '""') + '"';
  }

  document.getElementById("btn-csv").addEventListener("click", () => {
    if (cargados.length === 0) {
      Admin.avisar("No hay eventos para exportar.", "error");
      return;
    }
    const filas = [
      ["Fecha", "Usuario", "Acción", "Detalle", "IP", "Resultado"],
    ].concat(
      cargados.map((e) => [
        Admin.fecha(e.fecha),
        e.username || "",
        Admin.etiquetaAccion(e.accion),
        e.detalle || "",
        e.ip || "",
        e.exito ? "Correcto" : "Fallido",
      ]),
    );
    const csv =
      "\ufeff" + filas.map((f) => f.map(celdaCsv).join(",")).join("\r\n");
    const enlace = document.createElement("a");
    enlace.href = URL.createObjectURL(
      new Blob([csv], { type: "text/csv;charset=utf-8" }),
    );
    enlace.download = "auditoria-" + hoy() + ".csv";
    enlace.click();
    URL.revokeObjectURL(enlace.href);
    Admin.avisar("Exportados " + cargados.length + " eventos.", "ok");
  });

  await Promise.all([cargarAcciones(), cargarResumen()]);
  await cargar();
});
