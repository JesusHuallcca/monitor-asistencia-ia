const Admin = {
  yo: null,
  esSuper: false,
  _tAviso: null,

  PALETA: [
    ["#2f74ff", "#1747b8"],
    ["#12b5a5", "#0b7f74"],
    ["#8b5cf6", "#5b2fd6"],
    ["#f97316", "#c2410c"],
    ["#ec4899", "#be185d"],
    ["#22a35a", "#15703c"],
    ["#f5a524", "#c27a06"],
    ["#5b6b8c", "#2f3b57"],
  ],

  // Iconos fijos del menú (texto propio del código, no datos de usuarios)
  MENU: [
    {
      href: "usuarios.html",
      texto: "Usuarios",
      contador: true,
      icono:
        '<path d="M17 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="10" cy="7" r="4"/><path d="M21 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    },
    {
      href: "cursos.html",
      texto: "Cursos",
      icono:
        '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
    },
    {
      href: "auditoria.html",
      texto: "Auditoría",
      icono:
        '<path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><path d="M9 12h6M9 16h4"/>',
    },
    {
      href: "perfil.html",
      texto: "Perfil",
      icono:
        '<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1"/>',
    },
  ],

  ETIQUETAS: {
    login_ok: "Inicio de sesión",
    login_fallido: "Intento fallido",
    login_bloqueado: "Cuenta bloqueada",
    login_pendiente: "Cuenta en revisión",
    login_inactivo: "Cuenta desactivada",
    login_portal_incorrecto: "Portal incorrecto",
    login_facial_fallido: "Rostro no coincide",
    login_facial_sin_rostro: "Sin rostro habilitado",
    login_facial_vida: "Prueba de vida fallida",
    usuario_creado: "Usuario creado",
    estado_cambiado: "Estado cambiado",
    curso_creado: "Curso creado",
    curso_actualizado: "Curso actualizado",
    profesor_asignado: "Profesor asignado",
    profesor_quitado: "Profesor quitado",
    matricula_creada: "Estudiante matriculado",
    matricula_eliminada: "Matrícula eliminada",
    rostro_enrolado: "Rostro registrado",
    rostro_eliminado: "Rostro eliminado",
    rostro_duplicado: "Rostro duplicado",
    perfil_actualizado: "Perfil actualizado",
    password_cambiada: "Contraseña cambiada",
    password_cambio_fallido: "Cambio de contraseña fallido",
  },

  etiquetaAccion(accion) {
    return this.ETIQUETAS[accion] || accion;
  },

  // Verifica la sesión y que sea admin. Devuelve el usuario o null (y redirige).
  async iniciar() {
    if (!Auth.token()) {
      window.location.href = "login.html";
      return null;
    }
    const r = await Auth.fetchAutenticado("/api/users/me");
    if (!r.ok) {
      Auth.limpiar();
      window.location.href = "login.html";
      return null;
    }
    const yo = await r.json();
    if (!["admin", "superadmin"].includes(yo.rol)) {
      window.location.href = "../bienvenida.html";
      return null;
    }

    this.yo = yo;
    this.esSuper = yo.rol === "superadmin";
    this.construirMenu();
    document.getElementById("nombre-admin").textContent =
      yo.nombres + " " + yo.apellidos;
    document.getElementById("rol-admin").textContent = this.esSuper
      ? "Superadmin"
      : "Administrador";
    document.getElementById("btn-salir").addEventListener("click", () => {
      Auth.limpiar();
      window.location.href = "login.html";
    });
    this.refrescarPendientes();
    return yo;
  },

  construirMenu() {
    const nav = document.querySelector(".admin-menu nav");
    nav.replaceChildren();
    for (const item of this.MENU) {
      const a = document.createElement("a");
      a.href = item.href;
      if (window.location.pathname.endsWith(item.href))
        a.classList.add("activo");
      a.insertAdjacentHTML(
        "afterbegin",
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
          item.icono +
          "</svg>",
      );
      a.appendChild(document.createTextNode(item.texto));
      if (item.contador) {
        const c = this.el("span", "contador");
        c.id = "contador-pendientes";
        c.hidden = true;
        a.appendChild(c);
      }
      nav.appendChild(a);
    }
  },

  // Petición autenticada: si la sesión venció, vuelve al login
  async api(ruta, opciones) {
    const r = await Auth.fetchAutenticado(ruta, opciones);
    if (r.status === 401) {
      Auth.limpiar();
      window.location.href = "login.html";
    }
    return r;
  },

  async detalle(r, porDefecto) {
    const d = await r.json().catch(() => ({}));
    if (typeof d.detail === "string") return d.detail;
    if (Array.isArray(d.detail) && d.detail[0] && d.detail[0].msg) {
      return d.detail[0].msg.replace(/^Value error, /, "");
    }
    return porDefecto;
  },

  avisar(texto, tipo = "") {
    const aviso = document.getElementById("aviso");
    aviso.textContent = texto;
    aviso.className = "aviso " + tipo;
    aviso.hidden = false;
    clearTimeout(this._tAviso);
    this._tAviso = setTimeout(() => {
      aviso.hidden = true;
    }, 3500);
  },

  setPendientes(n) {
    const c = document.getElementById("contador-pendientes");
    if (!c) return;
    c.textContent = n;
    c.hidden = n === 0;
  },

  async refrescarPendientes() {
    const r = await Auth.fetchAutenticado(
      "/api/admin/usuarios?estado=pendiente&limit=200",
    );
    if (r.ok) this.setPendientes((await r.json()).length);
  },

  fecha(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleString("es-PE", {
      dateStyle: "short",
      timeStyle: "medium",
    });
  },

  el(etiqueta, clase, texto) {
    const e = document.createElement(etiqueta);
    if (clase) e.className = clase;
    if (texto !== undefined) e.textContent = texto;
    return e;
  },

  // Par de colores estable según un texto (para avatares y banners)
  colores(texto) {
    let h = 0;
    for (const c of texto) h = (h * 31 + c.charCodeAt(0)) % 997;
    return this.PALETA[h % this.PALETA.length];
  },

  avatar(nombres, apellidos, semilla) {
    const a = this.el(
      "span",
      "avatar",
      ((nombres[0] || "") + (apellidos[0] || "")).toUpperCase(),
    );
    a.style.background = this.colores(semilla)[0];
    return a;
  },
};
