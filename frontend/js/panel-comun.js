// Base común de los paneles de profesor y estudiante (hereda los ayudantes de Admin)
const Panel = Object.assign(Object.create(Admin), {
  INICIO: {
    estudiante: "../estudiante/inicio.html",
    profesor: "../profesor/cursos.html",
    admin: "../admin/usuarios.html",
    superadmin: "../admin/usuarios.html",
  },

  ICONOS: {
    inicio: '<path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>',
    libro:
      '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
    notas:
      '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M8 13h8M8 17h5"/>',
    asistencia:
      '<circle cx="12" cy="12" r="10"/><polyline points="9 12 12 15 16 10"/>',
    grafico: '<path d="M3 3v18h18"/><path d="M7 14l4-4 4 4 5-6"/>',
    ia: '<path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
    perfil:
      '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1"/>',
  },

  menuDe(rol) {
    const I = this.ICONOS;
    if (rol === "estudiante") {
      return [
        { href: "inicio.html", texto: "Inicio", icono: I.inicio },
        { href: "cursos.html", alias: ["curso.html"], texto: "Mis cursos", icono: I.libro },
        { href: "calificaciones.html", texto: "Mis calificaciones", icono: I.notas },
        { href: "asistencia.html", texto: "Mi asistencia", icono: I.asistencia },
        { href: "ia.html", texto: "Asistente IA", icono: I.ia },
        { href: "emoscan.html", texto: "EmoScan", icono: I.ia },
        { href: "perfil.html", texto: "Mi perfil", icono: I.perfil },
      ];
    }
    const base = [
      {
        href: "cursos.html",
        alias: ["curso.html"],
        texto: "Cursos",
        icono: I.libro,
      },
    ];
    if (rol === "profesor") {
      base.push({ href: "segmentacion.html", texto: "Segmentación IA", icono: I.ia });
      base.push({ href: 'estadistica.html', texto: 'Estadística Básica', icono: I.notas });
      base.push({ href: 'prediccion.html', texto: 'Predicción ML', icono: I.ia });
      base.push({ href: 'logistica.html', texto: 'Clasificación ML', icono: I.ia });
      base.push({ href: 'indicadores.html', texto: 'Dashboard ML', icono: I.grafico || I.ia });
      base.push({ href: 'red-neuronal.html', texto: 'Red Neuronal IA', icono: I.ia });
    }
    base.push({ href: "perfil.html", texto: "Perfil", icono: I.perfil });
    return base;
  },

  // Verifica la sesión y el rol. Si el rol no corresponde, manda al panel correcto.
  async iniciar(rol) {
    this.montarMenu(rol);
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
    this.montarChatbot();
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

  
  montarChatbot() {
    if (document.getElementById('monitor-chat-root')) return;
    if (!['estudiante', 'profesor', 'admin'].includes(this.yo?.rol)) return;

    if (!window.monitorReady) {
      const s1 = document.createElement('script');
      s1.src = '../js/chatbot-init.js';
      s1.onload = () => {
        if (!document.getElementById('monitor-chat-root')) {
          const s2 = document.createElement('script');
          s2.src = '../components/chatbot.js';
          document.body.appendChild(s2);
        }
      };
      document.body.appendChild(s1);
    } else {
      if (!document.getElementById('monitor-chat-root')) {
        const s2 = document.createElement('script');
        s2.src = '../components/chatbot.js';
        document.body.appendChild(s2);
      }
    }
  },

  montarMenu(rol) {
    const aside = document.querySelector(".admin-menu");
    if (!aside) return;
    this.montarBarraMovil(rol);
    aside.replaceChildren();

    if (rol === "estudiante") {
      // Diseño del nuevo sidebar de Estudiante
      aside.classList.add("dashboard-sidebar");

      const marca = this.el("div", "sidebar-brand");
      marca.innerHTML = `
        <div class="brand-icon-wrap">
          <svg viewBox="0 0 24 24" fill="currentColor" style="width:28px;height:28px;color:#fff;">
            <path d="M12 3L1 9l4 2.18v6L12 21l7-3.82v-6l2-1.09V17h2V9L12 3zm6.82 6L12 12.72 5.18 9 12 5.28 18.82 9zM17 15.99l-5 2.73-5-2.73v-3.72L12 15l5-2.73v3.72z"/>
          </svg>
        </div>
        <div class="brand-text">
          <span class="brand-title" style="font-size:15px;font-weight:800;color:#fff;">ASISTENCIA IA</span>
          <span class="brand-subtitle" style="font-size:11px;color:#94a3b8;">Campus Virtual</span>
        </div>
        <button type="button" class="btn-cerrar-drawer" aria-label="Cerrar menú" style="margin-left:auto;">✕</button>
      `;
      const btnCerrarEst = marca.querySelector(".btn-cerrar-drawer");
      if (btnCerrarEst) btnCerrarEst.addEventListener("click", () => this.cerrarMenuMovil());
      aside.appendChild(marca);

      const secTitulo = this.el("div", "sidebar-section-title", "Estudiante");
      aside.appendChild(secTitulo);

      const nav = document.createElement("nav");
      nav.className = "sidebar-nav";
      nav.setAttribute("aria-label", "Menú del estudiante");
      const ruta = window.location.pathname;

      for (const item of this.menuDe(rol)) {
        const a = document.createElement("a");
        a.href = item.href;
        a.className = "nav-link";
        if ([item.href, ...(item.alias || [])].some((h) => ruta.endsWith("/" + h))) {
          a.classList.add("active");
        }
        a.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;flex-shrink:0;">
            ${item.icono}
          </svg>
          <span>${item.texto}</span>
        `;
        nav.appendChild(a);
      }
      aside.appendChild(nav);

      const footer = this.el("div", "sidebar-footer");
      footer.innerHTML = `
        <div class="sidebar-footer-links">
          <a href="perfil.html" class="sidebar-footer-link">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;">
              <circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 1 0-16 0"/>
            </svg>
            Mi perfil
          </a>
          <button type="button" class="sidebar-footer-link" id="btn-logout-comun">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Cerrar sesión
          </button>
        </div>
        <div class="sidebar-campus-card" style="margin-top:10px;">
          <img src="../assets/img/campus_building.jpg" alt="Campus Moderno" style="width:100%;height:85px;object-fit:cover;border-radius:8px;display:block;" />
        </div>
      `;
      footer.querySelector("#btn-logout-comun").addEventListener("click", () => {
        Auth.limpiar();
        window.location.href = "../login.html";
      });
      aside.appendChild(footer);
      return;
    }

    // Menú clásico para profesor / admin
    const marca = this.el("div", "admin-marca");
    const logo = document.createElement("img");
    logo.src = "../assets/img/senati.png";
    logo.alt = "Senati";
    marca.appendChild(logo);

    const btnCerrar = this.el("button", "btn-cerrar-drawer", "✕");
    btnCerrar.type = "button";
    btnCerrar.setAttribute("aria-label", "Cerrar menú");
    btnCerrar.addEventListener("click", () => this.cerrarMenuMovil());
    marca.appendChild(btnCerrar);

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
    const nombreUsuario = this.yo
      ? (this.yo.nombres + " " + this.yo.apellidos)
      : (Auth.leer("nombre") || (rol === "profesor" ? "Profesor" : "Usuario"));
    quien.appendChild(
      this.el("strong", "", nombreUsuario),
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


  montarBarraMovil(rol) {
    if (document.querySelector(".admin-barra-movil")) return;

    const layout = document.querySelector(".admin-layout") || document.querySelector(".dashboard-layout");
    if (!layout) return;

    const barra = document.createElement("header");
    barra.className = "admin-barra-movil";

    const titulos = {
      estudiante: "Estudiante",
      profesor: "Profesor",
      admin: "Administrador",
      superadmin: "Superadmin"
    };
    const tituloRol = titulos[rol] || "Usuario";

    barra.innerHTML = `
      <button type="button" class="btn-hamburguesa" aria-label="Abrir menú" id="btn-toggle-menu">
        <svg viewBox="0 0 24 24" width="22" height="22" stroke="currentColor" stroke-width="2.2" fill="none">
          <line x1="3" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="6" x2="21" y2="6"></line>
          <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
      </button>
      <div class="barra-movil-marca">
        <img src="../assets/img/senati.png" alt="Senati" />
      </div>
      <div class="barra-movil-user">
        <span class="user-badge-rol">${tituloRol}</span>
      </div>
    `;

    let overlay = document.querySelector(".admin-overlay-movil");
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.className = "admin-overlay-movil";
      document.body.appendChild(overlay);
    }

    layout.parentNode.insertBefore(barra, layout);

    barra.querySelector("#btn-toggle-menu").addEventListener("click", () => this.toggleMenuMovil());
    overlay.addEventListener("click", () => this.cerrarMenuMovil());
  },

  toggleMenuMovil() {
    const aside = document.querySelector(".admin-menu") || document.querySelector(".dashboard-sidebar");
    const overlay = document.querySelector(".admin-overlay-movil");
    if (!aside) return;
    const abierto = aside.classList.toggle("abierto");
    aside.classList.toggle("open", abierto);
    if (overlay) overlay.classList.toggle("activo", abierto);
    document.body.style.overflow = abierto ? "hidden" : "";
  },

  cerrarMenuMovil() {
    const aside = document.querySelector(".admin-menu") || document.querySelector(".dashboard-sidebar");
    const overlay = document.querySelector(".admin-overlay-movil");
    if (aside) {
      aside.classList.remove("abierto");
      aside.classList.remove("open");
    }
    if (overlay) overlay.classList.remove("activo");
    document.body.style.overflow = "";
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
