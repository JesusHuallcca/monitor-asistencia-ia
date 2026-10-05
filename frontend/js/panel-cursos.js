document.addEventListener("DOMContentLoaded", async () => {
  const rol = document.body.dataset.rol;
  const yo = await Panel.iniciar(rol);
  if (!yo) return;
  const el = Panel.el.bind(Panel);

  const grid = document.getElementById("cursos-grid");
  const filtroQ = document.getElementById("filtro-q");
  let temporizador = null;

  // El estudiante ve su calificación actual en cada tarjeta
  async function mostrarNota(curso, chip) {
    const r = await Panel.api("/api/cursos/" + curso.id + "/mis-notas");
    if (!r.ok) return;
    const datos = await r.json();
    if (datos.promedio_actual !== null) {
      chip.textContent =
        curso.periodo + " · Nota " + Panel.formatoNota(datos.promedio_actual);
    }
  }

  function tarjeta(c) {
    const [c1, c2] = Panel.colores(c.codigo);
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
    const chip = el(
      "span",
      "chip",
      c.activo ? c.periodo : c.periodo + " · Inactivo",
    );
    pie.appendChild(chip);
    const abrir = el("a", "btn-mini", "Abrir");
    abrir.href = "curso.html?id=" + c.id;
    pie.appendChild(abrir);
    info.appendChild(pie);

    art.appendChild(info);
    if (rol === "estudiante") mostrarNota(c, chip);
    return art;
  }

  async function cargar() {
    const q = filtroQ.value.trim();
    const r = await Panel.api(
      "/api/cursos" + (q ? "?q=" + encodeURIComponent(q) : ""),
    );
    if (!r.ok) {
      Panel.avisar(
        await Panel.detalle(r, "No se pudo cargar tus cursos."),
        "error",
      );
      return;
    }
    const lista = await r.json();
    grid.replaceChildren();
    if (lista.length === 0) {
      grid.appendChild(
        el(
          "p",
          "sin-resultados",
          q
            ? "No hay cursos con ese nombre."
            : rol === "estudiante"
              ? "Aún no estás matriculado en ningún curso. Consulta con la administración."
              : "Aún no tienes cursos asignados. Consulta con la administración.",
        ),
      );
      return;
    }
    lista.forEach((c) => grid.appendChild(tarjeta(c)));
  }

  filtroQ.addEventListener("input", () => {
    clearTimeout(temporizador);
    temporizador = setTimeout(cargar, 300);
  });

  await cargar();
});
