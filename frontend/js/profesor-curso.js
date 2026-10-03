document.addEventListener("DOMContentLoaded", async () => {
  const yo = await Panel.iniciar("profesor");
  if (!yo) return;
  const el = Panel.el.bind(Panel);
  const JSON_CABECERA = { "Content-Type": "application/json" };
  const v = (id) => document.getElementById(id).value.trim();

  const id = Panel.parametro("id");
  if (!id || !/^\d+$/.test(id)) {
    window.location.href = "cursos.html";
    return;
  }

  let libro = { evaluaciones: [], alumnos: [] };

  // ---------- Datos del curso ----------
  const rCurso = await Panel.api("/api/cursos/" + id);
  if (!rCurso.ok) {
    Panel.avisar("No encontramos ese curso.", "error");
    setTimeout(() => {
      window.location.href = "cursos.html";
    }, 1200);
    return;
  }
  const curso = await rCurso.json();
  document.title = "Senati | " + curso.nombre;
  document.getElementById("curso-nombre").textContent = curso.nombre;
  document.getElementById("curso-sub").textContent =
    curso.codigo + " · " + curso.periodo;
  const rDoc = await Panel.api("/api/cursos/" + id + "/profesores");
  const docentes = rDoc.ok ? await rDoc.json() : [];
  const pintarContenido = () =>
    ContenidoCurso.pintar({ rol: "profesor", curso, docentes, libro });

  // ---------- Estudiantes ----------
  function pintarEstudiantes() {
    const cuerpo = document.getElementById("estudiantes-cuerpo");
    cuerpo.replaceChildren();
    if (libro.alumnos.length === 0) {
      const tr = el("tr");
      const td = el(
        "td",
        "vacio",
        "Aún no hay estudiantes matriculados en este curso.",
      );
      td.colSpan = 3;
      tr.appendChild(td);
      cuerpo.appendChild(tr);
      return;
    }
    for (const a of libro.alumnos) {
      const tr = el("tr");
      const tdP = el("td");
      const caja = el("div", "persona");
      caja.appendChild(Panel.avatar(a.nombres, a.apellidos, a.username));
      const t = el("div");
      t.appendChild(el("strong", "", a.apellidos + ", " + a.nombres));
      t.appendChild(el("small", "", "@" + a.username));
      caja.appendChild(t);
      tdP.appendChild(caja);
      tr.appendChild(tdP);
      tr.appendChild(el("td", "", a.codigo || "—"));
      tr.appendChild(
        el(
          "td",
          "nota-valor " + Panel.claseNota(a.promedio_actual),
          Panel.formatoNota(a.promedio_actual),
        ),
      );
      cuerpo.appendChild(tr);
    }
  }

  // ---------- Libro de calificaciones ----------
  function pintarLibro() {
    const cab = document.getElementById("libro-cabecera-fila");
    const cuerpo = document.getElementById("libro-cuerpo");
    cab.replaceChildren();
    cuerpo.replaceChildren();

    const suma = libro.evaluaciones.reduce((s, e) => s + e.peso, 0);
    const etiqueta = document.getElementById("suma-pesos");
    etiqueta.textContent =
      "Pesos asignados: " + Math.round(suma * 100) / 100 + " de 100";
    etiqueta.classList.toggle(
      "mal",
      libro.evaluaciones.length > 0 && Math.abs(suma - 100) > 0.01,
    );

    cab.appendChild(el("th", "col-alumno", "Estudiante"));
    for (const e of libro.evaluaciones) {
      const th = el("th");
      const caja = el("div", "th-eval");
      const t = el("div");
      t.appendChild(el("span", "", e.nombre));
      t.appendChild(
        el("small", "", e.peso + "% · " + Panel.fechaDia(e.fecha_vencimiento)),
      );
      caja.appendChild(t);
      const editar = el("button", "btn-mini", "Editar");
      editar.type = "button";
      editar.addEventListener("click", () => abrirEval(e));
      caja.appendChild(editar);
      th.appendChild(caja);
      cab.appendChild(th);
    }
    cab.appendChild(el("th", "", "Promedio"));

    const columnas = libro.evaluaciones.length + 2;
    if (libro.alumnos.length === 0 || libro.evaluaciones.length === 0) {
      const tr = el("tr");
      const td = el(
        "td",
        "vacio",
        libro.alumnos.length === 0
          ? "Aún no hay estudiantes matriculados en este curso."
          : "Aún no hay evaluaciones. Crea la primera con «+ Nueva evaluación».",
      );
      td.colSpan = columnas;
      tr.appendChild(td);
      cuerpo.appendChild(tr);
      return;
    }

    for (const a of libro.alumnos) {
      const tr = el("tr");
      const tdA = el("td", "col-alumno");
      const caja = el("div", "persona");
      caja.appendChild(Panel.avatar(a.nombres, a.apellidos, a.username));
      const t = el("div");
      t.appendChild(el("strong", "", a.apellidos + ", " + a.nombres));
      t.appendChild(el("small", "", a.codigo || "@" + a.username));
      caja.appendChild(t);
      tdA.appendChild(caja);
      tr.appendChild(tdA);

      for (const c of a.notas) {
        const ev = libro.evaluaciones.find((x) => x.id === c.evaluacion_id);
        const td = el("td");
        const texto =
          c.estado === "calificado"
            ? Panel.formatoNota(c.nota)
            : c.estado === "entregado"
              ? "Entregado"
              : "—";
        const clase =
          "celda-nota " +
          c.estado +
          (c.estado === "calificado" ? " " + Panel.claseNota(c.nota) : "");
        const b = el("button", clase, texto);
        b.type = "button";
        b.title = "Registrar nota";
        b.addEventListener("click", () => abrirNota(a, ev, c));
        td.appendChild(b);
        tr.appendChild(td);
      }

      tr.appendChild(
        el(
          "td",
          "nota-valor " + Panel.claseNota(a.promedio_actual),
          Panel.formatoNota(a.promedio_actual),
        ),
      );
      cuerpo.appendChild(tr);
    }
  }

  async function cargarLibro() {
    const r = await Panel.api("/api/cursos/" + id + "/libro");
    if (!r.ok) {
      Panel.avisar(
        await Panel.detalle(r, "No se pudo cargar el libro de calificaciones."),
        "error",
      );
      return;
    }
    libro = await r.json();
    pintarLibro();
    pintarEstudiantes();
    pintarContenido();
  }

  // ---------- Ventana: registrar nota ----------
  const modalNota = document.getElementById("modal-nota");
  const formNota = document.getElementById("form-nota");
  const msgNota = document.getElementById("msg-nota");
  const selEstado = document.getElementById("nota-estado");
  const inNota = document.getElementById("nota-valor");
  const campoNota = document.getElementById("campo-nota");
  const btnGuardarNota = document.getElementById("btn-guardar-nota");
  let notaCtx = null;

  const ajustarNota = () => {
    campoNota.hidden = selEstado.value !== "calificado";
  };
  selEstado.addEventListener("change", ajustarNota);

  function abrirNota(alumno, ev, celda) {
    notaCtx = { alumno, ev, celda };
    document.getElementById("nota-titulo").textContent =
      alumno.nombres + " " + alumno.apellidos;
    document.getElementById("nota-sub").textContent = ev.nombre;
    selEstado.value = celda.estado;
    inNota.value = celda.nota === null ? "" : String(celda.nota);
    msgNota.textContent = "";
    ajustarNota();
    modalNota.showModal();
    if (selEstado.value === "calificado") inNota.focus();
  }

  document
    .getElementById("btn-cancelar-nota")
    .addEventListener("click", () => modalNota.close());

  formNota.addEventListener("submit", async (e) => {
    e.preventDefault();
    msgNota.textContent = "";
    const estado = selEstado.value;
    let nota = null;
    if (estado === "calificado") {
      nota = parseFloat(inNota.value.trim().replace(",", "."));
      if (Number.isNaN(nota) || nota < 0 || nota > 20) {
        msgNota.textContent = "La nota debe ser un número entre 0 y 20.";
        return;
      }
    }

    btnGuardarNota.disabled = true;
    const r = await Panel.api(
      "/api/evaluaciones/" +
        notaCtx.ev.id +
        "/notas/" +
        notaCtx.alumno.usuario_id,
      {
        method: "PUT",
        headers: JSON_CABECERA,
        body: JSON.stringify({ estado, nota }),
      },
    );
    btnGuardarNota.disabled = false;

    if (!r.ok) {
      msgNota.textContent = await Panel.detalle(
        r,
        "No se pudo guardar la nota.",
      );
      return;
    }
    const res = await r.json();
    notaCtx.celda.estado = res.estado;
    notaCtx.celda.nota = res.nota;
    notaCtx.alumno.promedio_actual = res.promedio_actual;
    modalNota.close();
    pintarLibro();
    pintarEstudiantes();
    pintarContenido();
    Panel.avisar("Nota guardada.", "ok");
  });

  // ---------- Ventana: evaluación ----------
  const modalEval = document.getElementById("modal-eval");
  const formEval = document.getElementById("form-eval");
  const msgEval = document.getElementById("msg-eval");
  const btnGuardarEval = document.getElementById("btn-guardar-eval");
  const btnEliminarEval = document.getElementById("btn-eliminar-eval");
  let evalActual = null;

  function abrirEval(ev) {
    evalActual = ev || null;
    document.getElementById("eval-titulo").textContent = ev
      ? "Editar evaluación"
      : "Nueva evaluación";
    document.getElementById("eval-nombre").value = ev ? ev.nombre : "";
    document.getElementById("eval-fecha").value =
      ev && ev.fecha_vencimiento ? ev.fecha_vencimiento : "";
    document.getElementById("eval-peso").value = ev ? String(ev.peso) : "";
    btnEliminarEval.hidden = !ev;
    msgEval.textContent = "";
    modalEval.showModal();
  }

  document
    .getElementById("btn-nueva-eval")
    .addEventListener("click", () => abrirEval(null));
  document
    .getElementById("btn-cancelar-eval")
    .addEventListener("click", () => modalEval.close());

  formEval.addEventListener("submit", async (e) => {
    e.preventDefault();
    msgEval.textContent = "";
    if (v("eval-nombre").length < 3) {
      msgEval.textContent = "El nombre debe tener al menos 3 caracteres.";
      return;
    }
    const peso = parseFloat(v("eval-peso").replace(",", "."));
    if (Number.isNaN(peso) || peso < 0 || peso > 100) {
      msgEval.textContent = "El peso debe ser un número entre 0 y 100.";
      return;
    }

    const cuerpo = {
      nombre: v("eval-nombre"),
      fecha_vencimiento: v("eval-fecha") || null,
      peso,
    };
    btnGuardarEval.disabled = true;
    const r = evalActual
      ? await Panel.api("/api/evaluaciones/" + evalActual.id, {
          method: "PATCH",
          headers: JSON_CABECERA,
          body: JSON.stringify(cuerpo),
        })
      : await Panel.api("/api/cursos/" + id + "/evaluaciones", {
          method: "POST",
          headers: JSON_CABECERA,
          body: JSON.stringify(cuerpo),
        });
    btnGuardarEval.disabled = false;

    if (!r.ok) {
      msgEval.textContent = await Panel.detalle(
        r,
        "No se pudo guardar la evaluación.",
      );
      return;
    }
    modalEval.close();
    Panel.avisar(
      evalActual ? "Evaluación actualizada." : "Evaluación creada.",
      "ok",
    );
    await cargarLibro();
  });

  btnEliminarEval.addEventListener("click", async () => {
    if (!evalActual) return;
    if (
      !confirm(
        "¿Eliminar «" +
          evalActual.nombre +
          "»? También se borrarán las notas registradas en ella.",
      )
    )
      return;
    const r = await Panel.api("/api/evaluaciones/" + evalActual.id, {
      method: "DELETE",
    });
    if (!r.ok) {
      msgEval.textContent = await Panel.detalle(r, "No se pudo eliminar.");
      return;
    }
    modalEval.close();
    Panel.avisar("Evaluación eliminada.", "ok");
    await cargarLibro();
  });

  await cargarLibro();
  const mostrar = Panel.pestanas();
  mostrar(window.location.hash === "#notas" ? "notas" : "contenido");
});
