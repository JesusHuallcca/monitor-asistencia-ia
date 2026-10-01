const Auth = {
  // "Recordarme" usa localStorage (persiste); si no, sessionStorage (se borra al cerrar la pestaña).
  guardarSesion(datos, recordarme) {
    this.limpiar();
    const almacen = recordarme ? localStorage : sessionStorage;
    almacen.setItem("token", datos.access_token);
    almacen.setItem("rol", datos.rol);
    almacen.setItem("nombre", datos.nombre);
  },

  limpiar() {
    ["token", "rol", "nombre"].forEach((k) => {
      localStorage.removeItem(k);
      sessionStorage.removeItem(k);
    });
  },

  leer(clave) {
    return localStorage.getItem(clave) || sessionStorage.getItem(clave);
  },

  token() {
    return this.leer("token");
  },

  async login(ruta, identificador, password, recordarme) {
    let respuesta;
    try {
      respuesta = await fetch(API_URL + ruta, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identificador, password, recordarme }),
      });
    } catch (e) {
      throw new Error("No se pudo conectar con el servidor.");
    }

    const datos = await respuesta.json().catch(() => ({}));
    if (!respuesta.ok) {
      let mensaje = "No se pudo iniciar sesión.";
      if (typeof datos.detail === "string") mensaje = datos.detail;
      else if (Array.isArray(datos.detail))
        mensaje = "Revisa los datos ingresados.";
      throw new Error(mensaje);
    }
    return datos;
  },

  async fetchAutenticado(ruta, opciones = {}) {
    const cabeceras = {
      ...(opciones.headers || {}),
      Authorization: "Bearer " + this.token(),
    };
    return fetch(API_URL + ruta, { ...opciones, headers: cabeceras });
  },
};
