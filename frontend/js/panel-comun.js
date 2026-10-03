// Base común de los paneles de profesor y estudiante (hereda los ayudantes de Admin)
const Panel = Object.assign(Object.create(Admin), {
  INICIO: {
    estudiante: "../estudiante/cursos.html",
    profesor: "../profesor/cursos.html",
    admin: "../admin/usuarios.html",
    superadmin: "../admin/usuarios.html",
  },

  ICONOS: {
    libro:
      '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
    notas:
      '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M8 13h8M8 17h5"/>',
    ia: '<path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
    perfil:
      '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1"/>',
  },

  menuDe(rol) {
    const I = this.ICONOS;
    const base = [
      {
        href: "cursos.html",
        alias: ["curso.html"],
        texto: "Cursos",
        icono: I.libro,
      },
    ];
    if (rol === "estudiante") {
      base.push({
        href: "calificaciones.html",
        texto: "Calificaciones",
        icono: I.notas,
      });
      base.push({ href: "ia.html", texto: "Asistente IA", icono: I.ia });
    }
    base.push({ href: "perfil.html", texto: "Perfil", icono: I.perfil });
    return base;
  },

  // Verifica la sesión y el rol. Si el rol no corresponde, manda al panel correcto.
  async iniciar(rol) {
    if (!Auth.token()) {
      window.location.href = "../login.html";
      return null;
    }
    const r = await Auth.fetchAutenticado("/api/users/me");
    if (!r.ok) {
      Auth.limpiar();
      window.location.href = "../login.html";
      return null;
    }
    const yo = await r.json();
    if (yo.rol !== rol) {
      window.location.href = this.INICIO[yo.rol] || "../login.html";
      return null;
    }
    this.yo = yo;
    this.montarMenu(rol);
    return yo;
  },

  // Si la sesión venció, vuelve al login
  async api(ruta, opciones) {
    const r = await Auth.fetchAutenticado(ruta, opciones);
    if (r.status === 401) {
      Auth.limpiar();
      window.location.href = "../login.html";
    }
    return r;
  },

  montarMenu(rol) {
    const aside = document.querySelector(".admin-menu");
    aside.replaceChildren();

    const marca = this.el("div", "admin-marca");
    const logo = document.createElement("img");
    logo.src = "../assets/img/senati.png";
    logo.alt = "Senati";
    marca.appendChild(logo);
    aside.appendChild(marca);

    const nav = document.createElement("nav");
    nav.setAttribute("aria-label", "Menú principal");
    const ruta = window.location.pathname;
    for (const item of this.menuDe(rol)) {
      const a = document.createElement("a");
      a.href = item.href;
      if (
        [item.href, ...(item.alias || [])].some((h) => ruta.endsWith("/" + h))
      )
        a.classList.add("activo");
      a.insertAdjacentHTML(
        "afterbegin",
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
          item.icono +
          "</svg>",
      );
      a.appendChild(document.createTextNode(item.texto));
      nav.appendChild(a);
    }
    aside.appendChild(nav);

    const pie = this.el("div", "admin-pie");
    const quien = this.el("div", "quien-menu");
    quien.appendChild(
      this.el("strong", "", this.yo.nombres + " " + this.yo.apellidos),
    );
    quien.appendChild(
      this.el("span", "", rol === "profesor" ? "Profesor" : "Estudiante"),
    );
    pie.appendChild(quien);
    const salir = this.el("button", "btn-salir", "Cerrar sesión");
    salir.type = "button";
    salir.addEventListener("click", () => {
      Auth.limpiar();
      window.location.href = "../login.html";
    });
    pie.appendChild(salir);
    aside.appendChild(pie);
  },

  parametro(nombre) {
    return new URLSearchParams(window.location.search).get(nombre);
  },

  // Pestañas: botones .pestana[data-tab] y secciones #tab-<nombre>
  pestanas(alCambiar) {
    const botones = document.querySelectorAll(".pestana");
    const mostrar = (nombre) => {
      botones.forEach((b) => {
        const activa = b.dataset.tab === nombre;
        b.classList.toggle("activo", activa);
        b.setAttribute("aria-selected", String(activa));
      });
      document.querySelectorAll(".panel-pestana").forEach((p) => {
        p.hidden = p.id !== "tab-" + nombre;
      });
      if (alCambiar) alCambiar(nombre);
    };
    botones.forEach((b) =>
      b.addEventListener("click", () => mostrar(b.dataset.tab)),
    );
    return mostrar;
  },

  // Fecha "AAAA-MM-DD" sin desfase de zona horaria
  fechaDia(iso) {
    if (!iso) return "Sin fecha";
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(y, m - 1, d).toLocaleDateString("es-PE", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  },

  hoyIso() {
    const d = new Date();
    return (
      d.getFullYear() +
      "-" +
      String(d.getMonth() + 1).padStart(2, "0") +
      "-" +
      String(d.getDate()).padStart(2, "0")
    );
  },

  formatoNota(n) {
    return n === null || n === undefined
      ? "—"
      : String(Math.round(n * 100) / 100);
  },

  claseNota(n) {
    if (n === null || n === undefined) return "";
    return n >= 11 ? "aprobado" : "desaprobado";
  },

  vacio(titulo, texto) {
    const d = this.el("div", "vacio-bloque");
    d.appendChild(this.el("strong", "", titulo));
    d.appendChild(document.createTextNode(texto));
    return d;
  },

  pintarPersonas(ul, lista, textoVacio) {
    ul.replaceChildren();
    if (!lista.length) {
      ul.appendChild(this.el("li", "vacio-lista", textoVacio));
      return;
    }
    for (const p of lista) {
      const li = this.el("li");
      const caja = this.el("div", "persona");
      caja.appendChild(this.avatar(p.nombres, p.apellidos, p.username));
      const t = this.el("div");
      t.appendChild(this.el("strong", "", p.nombres + " " + p.apellidos));
      t.appendChild(this.el("small", "", p.detalle || "@" + p.username));
      caja.appendChild(t);
      li.appendChild(caja);
      ul.appendChild(li);
    }
  },
});
