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

  const [rCurso, rDocentes, rNotas, rAsistencia] = await Promise.all([
    Panel.api("/api/cursos/" + id),
    Panel.api("/api/cursos/" + id + "/profesores"),
    Panel.api("/api/cursos/" + id + "/mis-notas"),
    Panel.api("/api/attendance/my-course/" + id),
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

  const asistencia = rAsistencia.ok
    ? await rAsistencia.json()
    : {
        promedio: null,
        presentes: 0,
        registros: [],
      };

  document.title = "Senati | " + curso.nombre;

  document.getElementById("curso-nombre").textContent =
    curso.nombre;

  document.getElementById("curso-sub").textContent =
    curso.codigo + " · " + curso.periodo;

  // ---------- Contenido ----------
  ContenidoCurso.pintar({
    rol: "estudiante",
    curso,
    docentes,
    filas: notas.filas,
  });

  // ---------- Calendario ----------
  function pintarCalendario(filas) {
    const lista = document.getElementById("lista-calendario");

    lista.replaceChildren();

    const conFecha = filas
      .filter((f) => f.fecha_vencimiento)
      .sort((a, b) =>
        a.fecha_vencimiento.localeCompare(b.fecha_vencimiento),
      );

    if (conFecha.length === 0) {
      lista.appendChild(
        el(
          "li",
          "vacio-lista",
          "Este curso no tiene fechas de entrega.",
        ),
      );

      return;
    }

    const hoy = Panel.hoyIso();

    for (const f of conFecha) {
      const li = el("li");

      const izq = el("div");

      izq.appendChild(
        el("strong", "", f.nombre),
      );

      izq.appendChild(
        document.createElement("br"),
      );

      const vencida =
        f.fecha_vencimiento < hoy &&
        f.estado === "pendiente";

      izq.appendChild(
        el(
          "small",
          "",
          Panel.fechaDia(f.fecha_vencimiento) +
            (vencida ? " · Vencida" : ""),
        ),
      );

      li.appendChild(izq);

      li.appendChild(
        el(
          "span",
          "estado " + f.estado,
          ESTADOS[f.estado] || f.estado,
        ),
      );

      lista.appendChild(li);
    }
  }

  // ---------- Drawer de asistencia ----------
  function abrirDrawerAsistencia() {
    console.log("ABRIENDO DRAWER");
    const drawer = document.getElementById(
      "drawer-asistencia",
      
    );

    const nombre = document.getElementById(
      "asistencia-nombre",
    );

    const promedio = document.getElementById(
      "asistencia-promedio",
    );

    const presentes = document.getElementById(
      "asistencia-presentes",
    );

    const registros = document.getElementById(
      "asistencia-registros",
    );

    nombre.textContent =
      yo.nombres + " " + yo.apellidos;

    promedio.textContent =
      asistencia.promedio !== null
        ? asistencia.promedio + " / 100"
        : "—";

    presentes.textContent =
      asistencia.presentes || 0;

    registros.replaceChildren();

    if (asistencia.registros.length === 0) {
      registros.appendChild(
        el(
          "div",
          "asistencia-sin-registros",
          "Aún no hay registros de asistencia.",
        ),
      );
    } else {
      for (const registro of asistencia.registros) {
        const fila = el(
          "div",
          "asistencia-registro",
        );

        fila.appendChild(
          el(
            "span",
            "",
            Panel.fechaDia(registro.fecha),
          ),
        );

        fila.appendChild(
          el(
            "span",
            "asistencia-estado " +
              registro.estado.toLowerCase(),
            registro.estado,
          ),
        );

        fila.appendChild(
          el(
            "span",
            "",
            registro.calificacion + " %",
          ),
        );

        registros.appendChild(fila);
      }
    }

   drawer.classList.add("abierto");

console.log("DRAWER:", drawer);
console.log("CLASES:", drawer.className);

drawer.setAttribute(
  "aria-hidden",
  "false",
);

console.log(
  "ARIA:",
  drawer.getAttribute("aria-hidden"),
);
  }

  function cerrarDrawerAsistencia() {
    const drawer = document.getElementById(
      "drawer-asistencia",
    );

    drawer.classList.remove("abierto");

    drawer.setAttribute(
      "aria-hidden",
      "true",
    );
  }

  // ---------- Libro de calificaciones ----------
  function pintarLibro() {
    document.getElementById("libro-quien").textContent =
      yo.nombres + " " + yo.apellidos;

    const pastilla = document.getElementById(
      "libro-actual",
    );

    pastilla.textContent =
      Panel.formatoNota(notas.promedio_actual);

    pastilla.className =
      "nota-pastilla " +
      Panel.claseNota(notas.promedio_actual);

    const cuerpo = document.getElementById(
      "libro-cuerpo",
    );

    cuerpo.replaceChildren();

    for (const f of notas.filas) {
      const tr = el("tr");

      const tdNombre = el("td");

      tdNombre.appendChild(
        el("strong", "", f.nombre),
      );

      tdNombre.appendChild(
        document.createElement("br"),
      );

      tdNombre.appendChild(
        el(
          "small",
          "",
          "Peso " + f.peso + "%",
        ),
      );

      tr.appendChild(tdNombre);

      tr.appendChild(
        el(
          "td",
          "",
          Panel.fechaDia(f.fecha_vencimiento),
        ),
      );

      const tdEstado = el("td");

      tdEstado.appendChild(
        el(
          "span",
          "estado " + f.estado,
          ESTADOS[f.estado] || f.estado,
        ),
      );

      tr.appendChild(tdEstado);

      tr.appendChild(
        el(
          "td",
          "nota-valor " +
            (f.estado === "calificado"
              ? Panel.claseNota(f.nota)
              : ""),
          Panel.formatoNota(f.nota),
        ),
      );

      cuerpo.appendChild(tr);
    }

    // ---------- Asistencia ----------
    const trAsistencia = el(
      "tr",
      "fila-asistencia",
    );

    trAsistencia.setAttribute(
      "tabindex",
      "0",
    );

    trAsistencia.setAttribute(
      "role",
      "button",
    );

    trAsistencia.setAttribute(
      "aria-label",
      "Ver asistencia",
    );

    const tdNombreAsistencia = el("td");

    tdNombreAsistencia.appendChild(
      el(
        "strong",
        "",
        "Asistencia",
      ),
    );

    tdNombreAsistencia.appendChild(
      document.createElement("br"),
    );

    tdNombreAsistencia.appendChild(
      el(
        "small",
        "",
        "Control de asistencia",
      ),
    );

    trAsistencia.appendChild(
      tdNombreAsistencia,
    );

    trAsistencia.appendChild(
      el(
        "td",
        "",
        "Continuo",
      ),
    );

    const tdEstadoAsistencia = el("td");

    tdEstadoAsistencia.appendChild(
      el(
        "span",
        "estado",
        "Disponible",
      ),
    );

    trAsistencia.appendChild(
      tdEstadoAsistencia,
    );

    const calificacionAsistencia =
      asistencia.promedio !== null
        ? asistencia.promedio + " %"
        : "—";

    trAsistencia.appendChild(
      el(
        "td",
        "nota-valor",
        calificacionAsistencia,
      ),
    );

    // Toda la fila abre el drawer
 trAsistencia.addEventListener("click", () => {
  console.log("CLICK EN ASISTENCIA");
  abrirDrawerAsistencia();
});

    trAsistencia.addEventListener(
      "keydown",
      (event) => {
        if (
          event.key === "Enter" ||
          event.key === " "
        ) {
          event.preventDefault();
          abrirDrawerAsistencia();
        }
      },
    );

    cuerpo.appendChild(
      trAsistencia,
    );
  }

  // ---------- Cerrar drawer ----------
  document
    .getElementById(
      "cerrar-drawer-asistencia",
    )
    .addEventListener(
      "click",
      cerrarDrawerAsistencia,
    );

  // ---------- Inicialización ----------
  pintarCalendario(notas.filas);

  pintarLibro();

  const mostrar = Panel.pestanas();

  mostrar(
    window.location.hash === "#notas"
      ? "notas"
      : "contenido",
  );
});