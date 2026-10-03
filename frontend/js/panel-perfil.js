document.addEventListener("DOMContentLoaded", async () => {
  const rol = document.body.dataset.rol;
  const yo = await Panel.iniciar(rol);
  if (!yo) return;
  const el = Panel.el.bind(Panel);
  const esProfe = rol === "profesor";
  const JSON_CABECERA = { "Content-Type": "application/json" };
  const v = (id) => document.getElementById(id).value.trim();

  // El estudiante no puede cambiar su nombre; el profesor sí, y además su especialidad
  document.getElementById("campo-especialidad").hidden = !esProfe;
  if (!esProfe) {
    document.getElementById("d-nombres").disabled = true;
    document.getElementById("d-apellidos").disabled = true;
    document.getElementById("aviso-nombres").hidden = false;
  }

  // ---------- Resumen y formulario ----------
  function dato(dl, etiqueta, valor) {
    dl.appendChild(el("dt", "", etiqueta));
    dl.appendChild(el("dd", "", valor || "—"));
  }

  function pintar(p) {
    const avatar = Panel.avatar(p.nombres, p.apellidos, p.username);
    avatar.classList.add("avatar-grande");
    document.getElementById("perfil-avatar").replaceChildren(avatar);
    document.getElementById("p-nombre").textContent =
      p.nombres + " " + p.apellidos;
    document.getElementById("p-rol").textContent = esProfe
      ? "Profesor"
      : "Estudiante";

    const dl = document.getElementById("p-datos");
    dl.replaceChildren();
    dato(dl, "Usuario", "@" + p.username);
    dato(dl, "Correo", p.email);
    dato(dl, "Teléfono", p.telefono);
    if (esProfe) {
      dato(dl, "Especialidad", p.especialidad);
    } else {
      dato(dl, "Código", p.codigo);
      dato(dl, "Carrera", p.carrera);
      dato(dl, "Ciclo", p.ciclo ? String(p.ciclo) : "");
    }
    dato(dl, "Miembro desde", Panel.fecha(p.creado_en));
    dato(dl, "Último acceso", Panel.fecha(p.ultimo_login));

    document.getElementById("d-nombres").value = p.nombres;
    document.getElementById("d-apellidos").value = p.apellidos;
    document.getElementById("d-email").value = p.email;
    document.getElementById("d-telefono").value = p.telefono || "";
    document.getElementById("d-especialidad").value = p.especialidad || "";

    const f = document.getElementById("estado-facial");
    f.textContent = p.tiene_login_facial ? "Activado" : "Desactivado";
    f.className = "estado " + (p.tiene_login_facial ? "activo" : "inactivo");

    const menuNombre = document.querySelector(".quien-menu strong");
    if (menuNombre) menuNombre.textContent = p.nombres + " " + p.apellidos;
  }

  const r = await Panel.api("/api/users/me/perfil");
  if (r.ok) pintar(await r.json());
  else
    Panel.avisar(
      await Panel.detalle(r, "No se pudo cargar tu perfil."),
      "error",
    );

  // ---------- Guardar datos ----------
  const formDatos = document.getElementById("form-datos");
  const msgDatos = document.getElementById("msg-datos");
  const btnDatos = document.getElementById("btn-datos");

  formDatos.addEventListener("submit", async (e) => {
    e.preventDefault();
    msgDatos.textContent = "";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v("d-email"))) {
      msgDatos.textContent = "Ingresa un correo válido.";
      return;
    }
    if (!/^[0-9+\-\s()]{0,20}$/.test(v("d-telefono"))) {
      msgDatos.textContent =
        "El teléfono solo puede tener números, espacios, + - ( ).";
      return;
    }

    const cuerpo = { email: v("d-email"), telefono: v("d-telefono") };
    if (esProfe) {
      if (!v("d-nombres") || !v("d-apellidos")) {
        msgDatos.textContent = "Ingresa tus nombres y apellidos.";
        return;
      }
      cuerpo.nombres = v("d-nombres");
      cuerpo.apellidos = v("d-apellidos");
      cuerpo.especialidad = v("d-especialidad");
    }

    btnDatos.disabled = true;
    const rp = await Panel.api("/api/users/me/perfil", {
      method: "PATCH",
      headers: JSON_CABECERA,
      body: JSON.stringify(cuerpo),
    });
    btnDatos.disabled = false;

    if (!rp.ok) {
      msgDatos.textContent = await Panel.detalle(
        rp,
        "No se pudieron guardar los cambios.",
      );
      return;
    }
    pintar(await rp.json());
    Panel.avisar("Datos actualizados.", "ok");
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
  const TEXTO_BASE = "Mínimo 8 caracteres, con letras y números.";

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
      textoFuerza.textContent = TEXTO_BASE;
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
    const rc = await Panel.api("/api/users/me/password", {
      method: "POST",
      headers: JSON_CABECERA,
      body: JSON.stringify({ actual: inActual.value, nueva }),
    });
    btnClave.disabled = false;

    if (!rc.ok) {
      msgClave.textContent = await Panel.detalle(
        rc,
        "No se pudo cambiar la contraseña.",
      );
      return;
    }
    formClave.reset();
    barra.style.width = "0";
    textoFuerza.textContent = TEXTO_BASE;
    Panel.avisar("Contraseña actualizada.", "ok");
  });
});
