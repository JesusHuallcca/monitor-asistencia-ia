document.addEventListener("DOMContentLoaded", async () => {
  const yo = await Panel.iniciar("estudiante");
  if (!yo) return;
  const el = Panel.el.bind(Panel);
  const cuerpo = document.getElementById("tabla-cuerpo");

  const r = await Panel.api("/api/cursos");
  if (!r.ok) {
    Panel.avisar(
      await Panel.detalle(r, "No se pudo cargar tus cursos."),
      "error",
    );
    return;
  }
  const cursos = await r.json();

  const resultados = await Promise.all(
    cursos.map(async (c) => {
      const rn = await Panel.api("/api/cursos/" + c.id + "/mis-notas");
      return { curso: c, notas: rn.ok ? await rn.json() : null };
    }),
  );

  cuerpo.replaceChildren();
  if (resultados.length === 0) {
    const tr = el("tr");
    const td = el("td", "vacio", "Aún no estás matriculado en ningún curso.");
    td.colSpan = 4;
    tr.appendChild(td);
    cuerpo.appendChild(tr);
  }

  const promedios = [];
  for (const { curso, notas } of resultados) {
    const tr = el("tr");

    const tdCurso = el("td");
    tdCurso.appendChild(el("strong", "", curso.nombre));
    tdCurso.appendChild(document.createElement("br"));
    tdCurso.appendChild(el("small", "", curso.codigo + " · " + curso.periodo));
    tr.appendChild(tdCurso);

    const total = notas ? notas.filas.length : 0;
    const calificadas = notas
      ? notas.filas.filter((f) => f.estado === "calificado").length
      : 0;
    tr.appendChild(el("td", "", calificadas + " de " + total));

    const actual = notas ? notas.promedio_actual : null;
    if (actual !== null) promedios.push(actual);
    tr.appendChild(
      el(
        "td",
        "nota-valor " + Panel.claseNota(actual),
        Panel.formatoNota(actual),
      ),
    );

    const tdAbrir = el("td");
    const enlace = el("a", "btn-mini", "Ver libro");
    enlace.href = "curso.html?id=" + curso.id + "#notas";
    tdAbrir.appendChild(enlace);
    tr.appendChild(tdAbrir);

    cuerpo.appendChild(tr);
  }

  document.getElementById("st-cursos").textContent = resultados.length;
  document.getElementById("st-promedio").textContent = promedios.length
    ? Panel.formatoNota(promedios.reduce((a, b) => a + b, 0) / promedios.length)
    : "—";
});
