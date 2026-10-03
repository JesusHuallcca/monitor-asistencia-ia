document.addEventListener("DOMContentLoaded", async () => {
  const yo = await Panel.iniciar("estudiante");
  if (!yo) return;
  const el = Panel.el.bind(Panel);
  const ESTADOS = {
    pendiente: "Pendiente",
    entregado: "Entregado",
    calificado: "Calificado",
  };

  const id = Panel.parametro("id");
  if (!id || !/^\d+$/.test(id)) {
    window.location.href = "cursos.html";
    return;
  }

  const [rCurso, rDocentes, rNotas] = await Promise.all([
    Panel.api("/api/cursos/" + id),
    Panel.api("/api/cursos/" + id + "/profesores"),
    Panel.api("/api/cursos/" + id + "/mis-notas"),
  ]);

  if (!rCurso.ok || !rNotas.ok) {
    Panel.avisar("No encontramos ese curso.", "error");
    setTimeout(() => {
      window.location.href = "cursos.html";
    }, 1200);
    return;
  }

  const curso = await rCurso.json();
  const notas = await rNotas.json();
  const docentes = rDocentes.ok ? await rDocentes.json() : [];

  document.title = "Senati | " + curso.nombre;
  document.getElementById("curso-nombre").textContent = curso.nombre;
  document.getElementById("curso-sub").textContent =
    curso.codigo + " · " + curso.periodo;

  // ---------- Contenido ----------
  ContenidoCurso.pintar({
    rol: "estudiante",
    curso,
    docentes,
    filas: notas.filas,
  });

  // ---------- Calendario (fechas de entrega) ----------
  function pintarCalendario(filas) {
    const lista = document.getElementById("lista-calendario");
    lista.replaceChildren();
    const conFecha = filas
      .filter((f) => f.fecha_vencimiento)
      .sort((a, b) => a.fecha_vencimiento.localeCompare(b.fecha_vencimiento));
    if (conFecha.length === 0) {
      lista.appendChild(
        el("li", "vacio-lista", "Este curso no tiene fechas de entrega."),
      );
      return;
    }
    const hoy = Panel.hoyIso();
    for (const f of conFecha) {
      const li = el("li");
      const izq = el("div");
      izq.appendChild(el("strong", "", f.nombre));
      izq.appendChild(document.createElement("br"));
      const vencida = f.fecha_vencimiento < hoy && f.estado === "pendiente";
      izq.appendChild(
        el(
          "small",
          "",
          Panel.fechaDia(f.fecha_vencimiento) + (vencida ? " · Vencida" : ""),
        ),
      );
      li.appendChild(izq);
      li.appendChild(
        el("span", "estado " + f.estado, ESTADOS[f.estado] || f.estado),
      );
      lista.appendChild(li);
    }
  }

  // ---------- Libro de calificaciones ----------
  function pintarLibro() {
    document.getElementById("libro-quien").textContent =
      yo.nombres + " " + yo.apellidos;
    const pastilla = document.getElementById("libro-actual");
    pastilla.textContent = Panel.formatoNota(notas.promedio_actual);
    pastilla.className =
      "nota-pastilla " + Panel.claseNota(notas.promedio_actual);

    const cuerpo = document.getElementById("libro-cuerpo");
    cuerpo.replaceChildren();

    if (notas.filas.length === 0) {
      const tr = el("tr");
      const td = el("td", "vacio", "Este curso aún no tiene evaluaciones.");
      td.colSpan = 4;
      tr.appendChild(td);
      cuerpo.appendChild(tr);
      return;
    }

    for (const f of notas.filas) {
      const tr = el("tr");
      const tdNombre = el("td");
      tdNombre.appendChild(el("strong", "", f.nombre));
      tdNombre.appendChild(document.createElement("br"));
      tdNombre.appendChild(el("small", "", "Peso " + f.peso + "%"));
      tr.appendChild(tdNombre);
      tr.appendChild(el("td", "", Panel.fechaDia(f.fecha_vencimiento)));
      const tdEstado = el("td");
      tdEstado.appendChild(
        el("span", "estado " + f.estado, ESTADOS[f.estado] || f.estado),
      );
      tr.appendChild(tdEstado);
      tr.appendChild(
        el(
          "td",
          "nota-valor " +
            (f.estado === "calificado" ? Panel.claseNota(f.nota) : ""),
          Panel.formatoNota(f.nota),
        ),
      );
      cuerpo.appendChild(tr);
    }
  }

  pintarCalendario(notas.filas);
  pintarLibro();

  const mostrar = Panel.pestanas();
  mostrar(window.location.hash === "#notas" ? "notas" : "contenido");
});
