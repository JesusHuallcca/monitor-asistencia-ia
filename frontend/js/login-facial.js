document.addEventListener("DOMContentLoaded", () => {
  const btnRostro = document.getElementById("btn-rostro");
  const modal = document.getElementById("modal-rostro");
  const caja = document.getElementById("caja-video");
  const video = document.getElementById("video-rostro");
  const estado = document.getElementById("estado-rostro");
  const btnAccion = document.getElementById("btn-accion-rostro");
  const btnCerrar = document.getElementById("btn-cerrar-rostro");
  const mensaje = document.getElementById("mensaje");
  const inputIdent = document.getElementById("identificador");
  let ocupado = false;
  let paso = "activar";

  function mostrar(texto, tipo = "") {
    estado.textContent = texto;
    estado.className = "estado-camara " + tipo;
  }

  const alEstado = (e) => mostrar(e.texto, e.tipo);

  function pasoInicial() {
    paso = "activar";
    caja.classList.remove("activa");
    btnAccion.textContent = "Activar cámara";
    btnAccion.disabled = false;
    mostrar(
      "Necesitamos tu cámara para reconocer tu rostro. Tu navegador te pedirá permiso.",
    );
  }

  btnRostro.addEventListener("click", () => {
    mensaje.textContent = "";
    if (!inputIdent.value.trim()) {
      mensaje.textContent =
        "Escribe tu usuario o correo antes de entrar con rostro.";
      inputIdent.focus();
      return;
    }
    pasoInicial();
    modal.showModal();
  });

  btnCerrar.addEventListener("click", () => modal.close());
  modal.addEventListener("close", () => RostroVivo.detener(video)); // también al pulsar Esc

  btnAccion.addEventListener("click", async () => {
    if (ocupado) return;
    ocupado = true;
    btnAccion.disabled = true;

    try {
      if (paso === "activar") {
        await RostroVivo.cargar((t) => mostrar(t));
        mostrar("Solicitando permiso de cámara…");
        await RostroVivo.iniciar(video);
        caja.classList.add("activa");
        mostrar(
          "Ubica tu rostro frente a la cámara. Cuando los puntos estén verdes, pulsa Iniciar.",
        );
        btnAccion.textContent = "Iniciar verificación";
        paso = "verificar";
      } else {
        const [resultado] = await RostroVivo.ejecutar(
          [RostroVivo.accionAleatoria()],
          alEstado,
        );
        mostrar("Comparando tu rostro…");
        const datos = await Auth.loginFacial(
          inputIdent.value.trim(),
          resultado.frente,
        );
        Auth.guardarSesion(
          datos,
          document.getElementById("recordarme").checked,
        );
        RostroVivo.detener(video);
        mostrar("¡Listo! Entrando…", "ok");
        window.location.href = Auth.rutaInicio(datos.rol);
        return;
      }
    } catch (err) {
      if (err.message !== "cancelado") {
        mostrar(err.message, err.status === 403 ? "info" : "error");
        if (paso === "verificar") btnAccion.textContent = "Intentar de nuevo";
      }
    } finally {
      ocupado = false;
      btnAccion.disabled = false;
    }
  });
});
