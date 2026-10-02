document.addEventListener("DOMContentLoaded", async () => {
  if (!Auth.token()) {
    window.location.href = "login.html";
    return;
  }

  const video = document.getElementById("video-rostro");
  const caja = document.getElementById("caja-video");
  const estado = document.getElementById("estado-rostro");
  const etiqueta = document.getElementById("estado-login-facial");
  const btnAccion = document.getElementById("btn-accion-rostro");
  const btnDesactivar = document.getElementById("btn-desactivar");
  const consentimiento = document.getElementById("consentimiento");
  const cuenta = document.getElementById("cuenta-atras");
  let paso = "activar";
  let ocupado = false;

  const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

  function mostrar(texto, tipo = "") {
    estado.textContent = texto;
    estado.className = "estado-camara " + tipo;
  }

  async function detalle(respuesta, porDefecto) {
    const d = await respuesta.json().catch(() => ({}));
    return typeof d.detail === "string" ? d.detail : porDefecto;
  }

  async function cargarEstado() {
    const r = await Auth.fetchAutenticado("/api/face-auth/status");
    if (r.status === 401) {
      Auth.limpiar();
      window.location.href = "login.html";
      return;
    }
    if (!r.ok) {
      etiqueta.textContent = "No disponible";
      return;
    }
    const e = await r.json();
    etiqueta.textContent = e.activo
      ? "Login facial activado"
      : "Login facial desactivado";
    btnDesactivar.hidden = !e.activo;
    if (paso === "activar") {
      btnAccion.textContent = e.activo
        ? "Volver a registrar mi rostro"
        : "Activar cámara";
    }
  }

  async function registrar() {
    if (!consentimiento.checked) {
      mostrar("Debes aceptar el consentimiento para continuar.", "error");
      return;
    }
    const imagenes = [];
    for (let i = 1; i <= 3; i++) {
      mostrar(`Captura ${i} de 3: mira al frente.`);
      for (const n of [2, 1]) {
        cuenta.textContent = n;
        await esperar(700);
      }
      cuenta.textContent = "";
      imagenes.push(Camara.capturar(video));
      await esperar(300);
    }

    mostrar("Guardando tu rostro…");
    const r = await Auth.fetchAutenticado("/api/face-auth/enroll", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ consentimiento: true, imagenes }),
    });
    if (!r.ok)
      throw new Error(await detalle(r, "No se pudo registrar tu rostro."));

    Camara.detener(video);
    caja.classList.remove("activa");
    paso = "activar";
    mostrar("¡Listo! Ya puedes entrar con tu rostro.", "ok");
    await cargarEstado();
  }

  btnAccion.addEventListener("click", async () => {
    if (ocupado) return;
    ocupado = true;
    btnAccion.disabled = true;
    try {
      if (paso === "activar") {
        mostrar("Solicitando permiso de cámara…");
        await Camara.iniciar(video);
        caja.classList.add("activa");
        mostrar(
          "Centra tu rostro en el óvalo, con buena luz, y acepta el consentimiento.",
        );
        btnAccion.textContent = "Registrar mi rostro";
        paso = "registrar";
      } else {
        await registrar();
      }
    } catch (err) {
      mostrar(err.message, "error");
    } finally {
      ocupado = false;
      btnAccion.disabled = false;
    }
  });

  btnDesactivar.addEventListener("click", async () => {
    if (!confirm("¿Eliminar tu rostro guardado y desactivar el login facial?"))
      return;
    const r = await Auth.fetchAutenticado("/api/face-auth", {
      method: "DELETE",
    });
    if (r.ok) {
      mostrar("Login facial desactivado. Tu rostro fue eliminado.", "ok");
      await cargarEstado();
    } else {
      mostrar(await detalle(r, "No se pudo desactivar."), "error");
    }
  });

  window.addEventListener("pagehide", () => Camara.detener(video));
  await cargarEstado();
});
