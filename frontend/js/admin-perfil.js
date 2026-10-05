document.addEventListener("DOMContentLoaded", async () => {
  const yo = await Admin.iniciar();
  if (!yo) return;
  const el = Admin.el.bind(Admin);
  const JSON_CABECERA = { "Content-Type": "application/json" };
  const v = (id) => document.getElementById(id).value.trim();

  const NOMBRE_ROL = { superadmin: "Superadmin", admin: "Administrador" };

  // ---------- Resumen y formulario ----------
  function pintar(p) {
    const avatar = Admin.avatar(p.nombres, p.apellidos, p.username);
    avatar.classList.add("avatar-grande");
    document.getElementById("perfil-avatar").replaceChildren(avatar);

    document.getElementById("p-nombre").textContent =
      p.nombres + " " + p.apellidos;
    document.getElementById("p-rol").textContent = NOMBRE_ROL[p.rol] || p.rol;
    document.getElementById("p-usuario").textContent = "@" + p.username;
    document.getElementById("p-correo").textContent = p.email;
    document.getElementById("p-creado").textContent = Admin.fecha(p.creado_en);
    document.getElementById("p-ultimo").textContent = Admin.fecha(
      p.ultimo_login,
    );

    document.getElementById("d-nombres").value = p.nombres;
    document.getElementById("d-apellidos").value = p.apellidos;
    document.getElementById("d-email").value = p.email;
    document.getElementById("nombre-admin").textContent =
      p.nombres + " " + p.apellidos;
  }

  async function cargarPerfil() {
    const r = await Admin.api("/api/users/me/perfil");
    if (!r.ok) {
      Admin.avisar(
        await Admin.detalle(r, "No se pudo cargar tu perfil."),
        "error",
      );
      return;
    }
    pintar(await r.json());
  }

  // ---------- Guardar datos ----------
  const formDatos = document.getElementById("form-datos");
  const msgDatos = document.getElementById("msg-datos");
  const btnDatos = document.getElementById("btn-datos");

  formDatos.addEventListener("submit", async (e) => {
    e.preventDefault();
    msgDatos.textContent = "";
    if (!v("d-nombres") || !v("d-apellidos")) {
      msgDatos.textContent = "Ingresa tus nombres y apellidos.";
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v("d-email"))) {
      msgDatos.textContent = "Ingresa un correo válido.";
      return;
    }

    btnDatos.disabled = true;
    const r = await Admin.api("/api/users/me/perfil", {
      method: "PATCH",
      headers: JSON_CABECERA,
      body: JSON.stringify({
        nombres: v("d-nombres"),
        apellidos: v("d-apellidos"),
        email: v("d-email"),
      }),
    });
    btnDatos.disabled = false;

    if (!r.ok) {
      msgDatos.textContent = await Admin.detalle(
        r,
        "No se pudieron guardar los cambios.",
      );
      return;
    }
    pintar(await r.json());
    Admin.avisar("Datos actualizados.", "ok");
    cargarActividad();
  });

  // ---------- Cambiar contraseña ----------
  const formClave = document.getElementById("form-clave");
  const msgClave = document.getElementById("msg-clave");
  const btnClave = document.getElementById("btn-clave");
  const inActual = document.getElementById("c-actual");
  const inNueva = document.getElementById("c-nueva");
  const inRepetir = document.getElementById("c-repetir");
  const barra = document.getElementById("fuerza-barra");
  const textoFuerza = document.getElementById("fuerza-texto");

  document.getElementById("c-mostrar").addEventListener("change", (e) => {
    const tipo = e.target.checked ? "text" : "password";
    [inActual, inNueva, inRepetir].forEach((i) => {
      i.type = tipo;
    });
  });

  inNueva.addEventListener("input", () => {
    const c = inNueva.value;
    let puntos = 0;
    if (c.length >= 8) puntos++;
    if (c.length >= 12) puntos++;
    if (/[a-z]/.test(c) && /[A-Z]/.test(c)) puntos++;
    if (/\d/.test(c)) puntos++;
    if (/[^A-Za-z0-9]/.test(c)) puntos++;
    if (!c) {
      barra.style.width = "0";
      textoFuerza.textContent = "Mínimo 8 caracteres, con letras y números.";
      return;
    }
    const niveles = [
      ["Muy débil", "#d92d20"],
      ["Débil", "#d92d20"],
      ["Aceptable", "#f79009"],
      ["Buena", "#12b76a"],
      ["Fuerte", "#067647"],
      ["Muy fuerte", "#067647"],
    ];
    barra.style.width = (puntos / 5) * 100 + "%";
    barra.style.background = niveles[puntos][1];
    textoFuerza.textContent = "Seguridad: " + niveles[puntos][0];
  });

  formClave.addEventListener("submit", async (e) => {
    e.preventDefault();
    msgClave.textContent = "";
    const nueva = inNueva.value;
    if (!inActual.value) {
      msgClave.textContent = "Ingresa tu contraseña actual.";
      return;
    }
    if (nueva.length < 8 || !/[A-Za-z]/.test(nueva) || !/\d/.test(nueva)) {
      msgClave.textContent =
        "La nueva contraseña debe tener al menos 8 caracteres, con letras y números.";
      return;
    }
    if (nueva !== inRepetir.value) {
      msgClave.textContent = "Las contraseñas nuevas no coinciden.";
      return;
    }

    btnClave.disabled = true;
    const r = await Admin.api("/api/users/me/password", {
      method: "POST",
      headers: JSON_CABECERA,
      body: JSON.stringify({ actual: inActual.value, nueva }),
    });
    btnClave.disabled = false;

    if (!r.ok) {
      msgClave.textContent = await Admin.detalle(
        r,
        "No se pudo cambiar la contraseña.",
      );
      return;
    }
    formClave.reset();
    barra.style.width = "0";
    textoFuerza.textContent = "Mínimo 8 caracteres, con letras y números.";
    Admin.avisar("Contraseña actualizada.", "ok");
    cargarActividad();
  });

  // ---------- Actividad reciente ----------
  async function cargarActividad() {
    const lista = document.getElementById("actividad");
    const r = await Admin.api(
      "/api/admin/auditoria?usuario_id=" + yo.id + "&limit=6",
    );
    lista.replaceChildren();
    if (!r.ok) {
      lista.appendChild(
        el("li", "vacio-lista", "No se pudo cargar la actividad."),
      );
      return;
    }
    const eventos = await r.json();
    if (eventos.length === 0) {
      lista.appendChild(el("li", "vacio-lista", "Sin actividad registrada."));
      return;
    }
    for (const e of eventos) {
      const li = el("li");
      const izq = el("div");
      izq.appendChild(el("strong", "", Admin.etiquetaAccion(e.accion)));
      izq.appendChild(document.createElement("br"));
      izq.appendChild(
        el("small", "", Admin.fecha(e.fecha) + (e.ip ? " · " + e.ip : "")),
      );
      li.appendChild(izq);
      li.appendChild(
        el(
          "span",
          "estado " + (e.exito ? "activo" : "fallo"),
          e.exito ? "Correcto" : "Fallido",
        ),
      );
      lista.appendChild(li);
    }
  }

  await Promise.all([cargarPerfil(), cargarActividad()]);
});
