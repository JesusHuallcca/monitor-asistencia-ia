document.addEventListener("DOMContentLoaded", async () => {
  const yo = await Admin.iniciar();
  if (!yo) return;
  const el = Admin.el.bind(Admin);

  const grid = document.getElementById("cursos-grid");
  const filtroQ = document.getElementById("filtro-q");
  const JSON_CABECERA = { "Content-Type": "application/json" };
  let temporizador = null;

  // ---------- Lista de cursos ----------
  function tarjeta(c) {
    const [c1, c2] = Admin.colores(c.codigo);
    const art = el("article", "curso-card" + (c.activo ? "" : " inactivo"));

    const banner = el("div", "curso-banner");
    banner.style.setProperty("--c1", c1);
    banner.style.setProperty("--c2", c2);
    banner.dataset.sigla = c.codigo.split("-")[0];
    banner.appendChild(el("span", "curso-codigo", c.codigo));
    art.appendChild(banner);

    const info = el("div", "curso-info");
    info.appendChild(el("h3", "", c.nombre));
    info.appendChild(
      el("p", "curso-desc", c.descripcion || "Sin descripción."),
    );

    const pie = el("div", "curso-pie");
    pie.appendChild(
      el("span", "chip", c.activo ? c.periodo : c.periodo + " · Inactivo"),
    );
    const boton = el("button", "btn-mini", "Gestionar");
    boton.type = "button";
    boton.addEventListener("click", () => abrir(c));
    pie.appendChild(boton);
    info.appendChild(pie);

    art.appendChild(info);
    return art;
  }

  async function cargar() {
    const q = filtroQ.value.trim();
    const r = await Admin.api(
      "/api/cursos" + (q ? "?q=" + encodeURIComponent(q) : ""),
    );
    if (!r.ok) {
      Admin.avisar(
        await Admin.detalle(r, "No se pudo cargar los cursos."),
        "error",
      );
      return;
    }
    const lista = await r.json();
    grid.replaceChildren();
    if (lista.length === 0) {
      grid.appendChild(
        el("p", "sin-resultados", "No hay cursos con ese filtro."),
      );
      return;
    }
    lista.forEach((c) => grid.appendChild(tarjeta(c)));
  }

  filtroQ.addEventListener("input", () => {
    clearTimeout(temporizador);
    temporizador = setTimeout(cargar, 300);
  });

  // ---------- Nuevo curso ----------
  const modalNuevo = document.getElementById("modal-nuevo-curso");
  const formCurso = document.getElementById("form-curso");
  const msgCurso = document.getElementById("mensaje-curso");
  const btnGuardarCurso = document.getElementById("btn-guardar-curso");
  const v = (id) => document.getElementById(id).value.trim();

  document.getElementById("btn-nuevo-curso").addEventListener("click", () => {
    formCurso.reset();
    msgCurso.textContent = "";
    modalNuevo.showModal();
  });

  document
    .getElementById("btn-cancelar-curso")
    .addEventListener("click", () => modalNuevo.close());

  function validarCurso() {
    if (!/^[A-Za-z0-9-]{3,20}$/.test(v("c-codigo"))) {
      return "El código debe tener de 3 a 20 caracteres: letras, números o guion.";
    }
    if (v("c-nombre").length < 3)
      return "El nombre del curso debe tener al menos 3 caracteres.";
    if (v("c-periodo").length < 3)
      return "Ingresa el periodo (por ejemplo 2026-II).";
    return null;
  }

  formCurso.addEventListener("submit", async (e) => {
    e.preventDefault();
    msgCurso.textContent = "";
    const error = validarCurso();
    if (error) {
      msgCurso.textContent = error;
      return;
    }

    btnGuardarCurso.disabled = true;
    const r = await Admin.api("/api/cursos", {
      method: "POST",
      headers: JSON_CABECERA,
      body: JSON.stringify({
        codigo: v("c-codigo"),
        nombre: v("c-nombre"),
        periodo: v("c-periodo"),
        descripcion: v("c-descripcion") || null,
      }),
    });
    btnGuardarCurso.disabled = false;

    if (!r.ok) {
      msgCurso.textContent = await Admin.detalle(
        r,
        "No se pudo crear el curso.",
      );
      return;
    }

    const creado = await r.json();
    modalNuevo.close();
    Admin.avisar(
      "Curso " + creado.codigo + " creado. Ahora asígnale un profesor.",
      "ok",
    );
    await cargar();
    abrir(creado);
  });

  // ---------- Gestionar curso ----------
  const modal = document.getElementById("modal-curso");
  const lista = document.getElementById("lista-personas");
  const selAgregar = document.getElementById("sel-agregar");
  const btnAgregar = document.getElementById("btn-agregar");
  const btnToggle = document.getElementById("btn-toggle-activo");
  const tabs = document.querySelectorAll(".tab");
  const ROL_DE = { profesores: "profesor", estudiantes: "estudiante" };
  const SINGULAR = { profesores: "profesor", estudiantes: "estudiante" };
  let actual = null;
  let pestana = "profesores";
  let versionCarga = 0;

  function encabezado() {
    document.getElementById("curso-sub").textContent =
      actual.codigo + " · " + actual.periodo;
    document.getElementById("curso-titulo").textContent = actual.nombre;
    btnToggle.textContent = actual.activo
      ? "Desactivar curso"
      : "Activar curso";
  }

  function filaPersona(p) {
    const li = el("li");
    const caja = el("div", "persona");
    caja.appendChild(Admin.avatar(p.nombres, p.apellidos, p.username));
    const texto = el("div");
    texto.appendChild(el("strong", "", p.nombres + " " + p.apellidos));
    texto.appendChild(el("small", "", p.detalle || "@" + p.username));
    caja.appendChild(texto);
    li.appendChild(caja);

    const quitar = el("button", "btn-mini peligro", "Quitar");
    quitar.type = "button";
    quitar.addEventListener("click", () => quitarPersona(p, quitar));
    li.appendChild(quitar);
    return li;
  }

  function llenarSelect(candidatos, actuales) {
    const yaEstan = new Set(actuales.map((a) => a.usuario_id));
    const libres = candidatos.filter((c) => !yaEstan.has(c.id));
    selAgregar.replaceChildren();

    const base = el(
      "option",
      "",
      libres.length
        ? "Selecciona un " + SINGULAR[pestana] + "…"
        : "No hay más " + pestana + " activos",
    );
    base.value = "";
    selAgregar.appendChild(base);

    libres.forEach((c) => {
      const o = el(
        "option",
        "",
        c.apellidos + ", " + c.nombres + " (@" + c.username + ")",
      );
      o.value = c.id;
      selAgregar.appendChild(o);
    });
    selAgregar.disabled = libres.length === 0;
    btnAgregar.disabled = libres.length === 0;
  }

  async function cargarPestana() {
    const mia = ++versionCarga;
    lista.replaceChildren(el("li", "vacio-lista", "Cargando…"));

    const [rActuales, rCandidatos] = await Promise.all([
      Admin.api("/api/cursos/" + actual.id + "/" + pestana),
      Admin.api(
        "/api/admin/usuarios?rol=" +
          ROL_DE[pestana] +
          "&estado=activo&limit=200",
      ),
    ]);
    if (mia !== versionCarga) return; // el usuario cambió de pestaña mientras cargaba

    if (!rActuales.ok || !rCandidatos.ok) {
      lista.replaceChildren(
        el("li", "vacio-lista", "No se pudo cargar la lista."),
      );
      return;
    }
    const actuales = await rActuales.json();
    const candidatos = await rCandidatos.json();
    if (mia !== versionCarga) return;

    lista.replaceChildren();
    if (actuales.length === 0) {
      lista.appendChild(
        el("li", "vacio-lista", "Aún no hay " + pestana + " en este curso."),
      );
    } else {
      actuales.forEach((p) => lista.appendChild(filaPersona(p)));
    }
    llenarSelect(candidatos, actuales);
  }

  function abrir(curso) {
    actual = curso;
    pestana = "profesores";
    tabs.forEach((t) =>
      t.classList.toggle("activo", t.dataset.tab === pestana),
    );
    encabezado();
    modal.showModal();
    cargarPestana();
  }

  tabs.forEach((t) =>
    t.addEventListener("click", () => {
      pestana = t.dataset.tab;
      tabs.forEach((x) => x.classList.toggle("activo", x === t));
      cargarPestana();
    }),
  );

  async function quitarPersona(p, boton) {
    boton.disabled = true;
    const r = await Admin.api(
      "/api/cursos/" + actual.id + "/" + pestana + "/" + p.usuario_id,
      { method: "DELETE" },
    );
    if (r.ok) {
      Admin.avisar(p.username + " fue quitado del curso.", "ok");
      await cargarPestana();
    } else {
      Admin.avisar(await Admin.detalle(r, "No se pudo quitar."), "error");
      boton.disabled = false;
    }
  }

  btnAgregar.addEventListener("click", async () => {
    const id = parseInt(selAgregar.value, 10);
    if (!id) {
      Admin.avisar("Selecciona a quién agregar.", "error");
      return;
    }

    btnAgregar.disabled = true;
    const r = await Admin.api("/api/cursos/" + actual.id + "/" + pestana, {
      method: "POST",
      headers: JSON_CABECERA,
      body: JSON.stringify({ usuario_id: id }),
    });
    if (r.ok) {
      Admin.avisar(
        pestana === "profesores"
          ? "Profesor asignado."
          : "Estudiante matriculado.",
        "ok",
      );
    } else {
      Admin.avisar(await Admin.detalle(r, "No se pudo agregar."), "error");
    }
    await cargarPestana();
  });

  btnToggle.addEventListener("click", async () => {
    const r = await Admin.api("/api/cursos/" + actual.id, {
      method: "PATCH",
      headers: JSON_CABECERA,
      body: JSON.stringify({ activo: !actual.activo }),
    });
    if (r.ok) {
      actual = await r.json();
      encabezado();
      Admin.avisar(
        actual.activo ? "Curso activado." : "Curso desactivado.",
        "ok",
      );
      await cargar();
    } else {
      Admin.avisar(
        await Admin.detalle(r, "No se pudo cambiar el estado del curso."),
        "error",
      );
    }
  });

  document
    .getElementById("btn-cerrar-curso")
    .addEventListener("click", () => modal.close());

  await cargar();
});
