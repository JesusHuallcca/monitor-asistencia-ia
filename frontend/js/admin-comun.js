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
    c.textContent = n;
    c.hidden = n === 0;
  },

  async refrescarPendientes() {
    const r = await Auth.fetchAutenticado(
      "/api/admin/usuarios?estado=pendiente&limit=200",
    );
    if (r.ok) this.setPendientes((await r.json()).length);
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
