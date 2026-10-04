document.addEventListener("DOMContentLoaded", async () => {
  const yo = await Admin.iniciar();
  if (!yo) return;
  const el = Admin.el.bind(Admin);

  // Solo el superadmin puede crear administradores
  if (!Admin.esSuper)
    document.querySelector('#n-rol option[value="admin"]').remove();

  const cuerpo = document.getElementById("tabla-cuerpo");
  const filtroQ = document.getElementById("filtro-q");
  const filtroRol = document.getElementById("filtro-rol");
  const filtroEstado = document.getElementById("filtro-estado");
  let temporizador = null;

  const NOMBRE_ROL = {
    superadmin: "Superadmin",
    admin: "Administrador",
    profesor: "Profesor",
    estudiante: "Estudiante",
  };
  const NOMBRE_ESTADO = {
    activo: "Activo",
    pendiente: "Pendiente",
    inactivo: "Inactivo",
  };
  // Las tarjetas de resumen funcionan como filtros rápidos
  document.querySelectorAll(".stat").forEach((tarjeta) => {
    tarjeta.addEventListener("click", () => {
      filtroRol.value = tarjeta.dataset.rol;
      filtroEstado.value = tarjeta.dataset.estado;
      filtroQ.value = "";
      cargar();
    });
  });
  // ---------- Resumen ----------
  async function cargarStats() {
    const r = await Admin.api("/api/admin/usuarios?limit=200");
    if (!r.ok) return;
    const t = await r.json();
    const pendientes = t.filter((u) => u.estado === "pendiente").length;
    document.getElementById("st-total").textContent = t.length;
    document.getElementById("st-prof").textContent = t.filter(
      (u) => u.rol === "profesor",
    ).length;
    document.getElementById("st-est").textContent = t.filter(
      (u) => u.rol === "estudiante",
    ).length;
    document.getElementById("st-pend").textContent = pendientes;
    Admin.setPendientes(pendientes);
  }

  // ---------- Tabla ----------
  function celdaPersona(u) {
    const td = el("td");
    const caja = el("div", "persona");
    caja.appendChild(Admin.avatar(u.nombres, u.apellidos, u.username));
    const texto = el("div");
    texto.appendChild(el("strong", "", u.nombres + " " + u.apellidos));
    texto.appendChild(el("small", "", "@" + u.username));
    caja.appendChild(texto);
    td.appendChild(caja);
    return td;
  }

  function botonAccion(texto, clase, usuario, estado) {
    const b = el("button", "btn-mini " + clase, texto);
    b.type = "button";
    b.addEventListener("click", () => cambiarEstado(usuario, estado, b));
    return b;
  }

  function celdaAcciones(u) {
    const td = el("td");
    const caja = el("div", "acciones-fila");
    const protegido =
      u.id === yo.id ||
      u.rol === "superadmin" ||
      (u.rol === "admin" && !Admin.esSuper);
    if (!protegido) {
      if (u.estado === "pendiente")
        caja.appendChild(botonAccion("Aprobar", "ok", u, "activo"));
      if (u.estado === "inactivo")
        caja.appendChild(botonAccion("Activar", "ok", u, "activo"));
      if (u.estado !== "inactivo")
        caja.appendChild(botonAccion("Desactivar", "peligro", u, "inactivo"));
    }
    td.appendChild(caja);
    return td;
  }

  function dibujar(lista) {
    document.getElementById("conteo").textContent =
      lista.length + (lista.length === 1 ? " usuario" : " usuarios");
    cuerpo.replaceChildren();
    if (lista.length === 0) {
      const tr = el("tr");
      const td = el("td", "vacio", "No hay usuarios con ese filtro.");
      td.colSpan = 5;
      tr.appendChild(td);
      cuerpo.appendChild(tr);
      return;
    }
    for (const u of lista) {
      const tr = el("tr");
      tr.appendChild(celdaPersona(u));
      tr.appendChild(el("td", "", u.email));

      const tdRol = el("td");
      tdRol.appendChild(el("span", "badge", NOMBRE_ROL[u.rol] || u.rol));
      tr.appendChild(tdRol);

      const tdEstado = el("td");
      tdEstado.appendChild(
        el("span", "estado " + u.estado, NOMBRE_ESTADO[u.estado] || u.estado),
      );
      tr.appendChild(tdEstado);

      tr.appendChild(celdaAcciones(u));
      cuerpo.appendChild(tr);
    }
  }

  async function cargar() {
    const p = new URLSearchParams({ limit: "200" });
    if (filtroRol.value) p.set("rol", filtroRol.value);
    if (filtroEstado.value) p.set("estado", filtroEstado.value);
    if (filtroQ.value.trim()) p.set("q", filtroQ.value.trim());

    const r = await Admin.api("/api/admin/usuarios?" + p.toString());
    if (!r.ok) {
      Admin.avisar(
        await Admin.detalle(r, "No se pudo cargar la lista."),
        "error",
      );
      return;
    }
    dibujar(await r.json());
  }

  async function cambiarEstado(u, estado, boton) {
    boton.disabled = true;
    const r = await Admin.api("/api/admin/usuarios/" + u.id + "/estado", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ estado }),
    });
    if (r.ok) {
      Admin.avisar(
        estado === "activo"
          ? u.username + " ahora está activo."
          : u.username + " fue desactivado.",
        "ok",
      );
      await Promise.all([cargar(), cargarStats()]);
    } else {
      Admin.avisar(
        await Admin.detalle(r, "No se pudo cambiar el estado."),
        "error",
      );
      boton.disabled = false;
    }
  }

  filtroRol.addEventListener("change", cargar);
  filtroEstado.addEventListener("change", cargar);
  filtroQ.addEventListener("input", () => {
    clearTimeout(temporizador);
    temporizador = setTimeout(cargar, 300);
  });

  // ---------- Nuevo usuario ----------
  const modal = document.getElementById("modal-nuevo");
  const form = document.getElementById("form-nuevo");
  const msgNuevo = document.getElementById("mensaje-nuevo");
  const selRol = document.getElementById("n-rol");
  const boxEstudiante = document.getElementById("campos-estudiante");
  const boxProfesor = document.getElementById("campos-profesor");
  const btnGuardar = document.getElementById("btn-guardar-nuevo");
  const v = (id) => document.getElementById(id).value.trim();

  function ajustarCampos() {
    boxEstudiante.hidden = selRol.value !== "estudiante";
    boxProfesor.hidden = selRol.value !== "profesor";
  }

  function generarClave() {
    const letras = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz";
    const numeros = "23456789";
    const todo = letras + numeros;
    const bytes = new Uint32Array(12);
    crypto.getRandomValues(bytes);
    const cuerpoClave = Array.from(bytes, (b) => todo[b % todo.length]).join(
      "",
    );
    // Garantiza al menos una letra y un número
    return (
      letras[bytes[0] % letras.length] +
      numeros[bytes[1] % numeros.length] +
      cuerpoClave.slice(2)
    );
  }

  selRol.addEventListener("change", ajustarCampos);
  document.getElementById("btn-generar").addEventListener("click", () => {
    document.getElementById("n-password").value = generarClave();
  });

  document.getElementById("btn-nuevo").addEventListener("click", () => {
    form.reset();
    msgNuevo.textContent = "";
    ajustarCampos();
    modal.showModal();
  });

  document
    .getElementById("btn-cancelar-nuevo")
    .addEventListener("click", () => modal.close());

  function validarNuevo() {
    if (!v("n-nombres") || !v("n-apellidos"))
      return "Ingresa nombres y apellidos.";
    if (!/^[A-Za-z0-9._-]{3,50}$/.test(v("n-username"))) {
      return "El usuario debe tener de 3 a 50 caracteres: letras, números, punto, guion o guion bajo.";
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v("n-email")))
      return "Ingresa un correo válido.";
    const p = document.getElementById("n-password").value;
    if (p.length < 8 || !/[A-Za-z]/.test(p) || !/\d/.test(p)) {
      return "La contraseña debe tener al menos 8 caracteres, con letras y números.";
    }
    if (
      selRol.value === "estudiante" &&
      v("n-ciclo") &&
      !/^([1-9]|1[0-2])$/.test(v("n-ciclo"))
    ) {
      return "El ciclo debe ser un número del 1 al 12.";
    }
    return null;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    msgNuevo.textContent = "";
    const error = validarNuevo();
    if (error) {
      msgNuevo.textContent = error;
      return;
    }

    const rol = selRol.value;
    const nuevo = {
      rol,
      username: v("n-username"),
      email: v("n-email"),
      password: document.getElementById("n-password").value,
      nombres: v("n-nombres"),
      apellidos: v("n-apellidos"),
    };
    if (rol === "estudiante") {
      nuevo.carrera = v("n-carrera") || null;
      nuevo.ciclo = v("n-ciclo") ? parseInt(v("n-ciclo"), 10) : null;
    }
    if (rol === "profesor") nuevo.especialidad = v("n-especialidad") || null;

    btnGuardar.disabled = true;
    const r = await Admin.api("/api/admin/usuarios", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(nuevo),
    });
    btnGuardar.disabled = false;

    if (!r.ok) {
      msgNuevo.textContent = await Admin.detalle(
        r,
        "No se pudo crear el usuario.",
      );
      return;
    }

    modal.close();
    Admin.avisar(
      "Usuario " + nuevo.username + " creado. Entrégale su contraseña inicial.",
      "ok",
    );
    await Promise.all([cargar(), cargarStats()]);
  });

  await Promise.all([cargar(), cargarStats()]);
});
