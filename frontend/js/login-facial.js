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

  function mostrar(texto, tipo = "") {
    estado.textContent = texto;
    estado.className = "estado-camara " + tipo;
  }

  function pasoInicial() {
    caja.classList.remove("activa");
    btnAccion.textContent = "Activar cámara";
    btnAccion.dataset.paso = "activar";
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
  modal.addEventListener("close", () => Camara.detener(video)); // también al pulsar Esc

  btnAccion.addEventListener("click", async () => {
    if (ocupado) return;
    ocupado = true;
    btnAccion.disabled = true;

    try {
      if (btnAccion.dataset.paso === "activar") {
        mostrar("Solicitando permiso de cámara…");
        await Camara.iniciar(video);
        caja.classList.add("activa");
        mostrar(
          "Centra tu rostro en el óvalo, con buena luz, y pulsa Verificar.",
        );
        btnAccion.textContent = "Verificar rostro";
        btnAccion.dataset.paso = "verificar";
      } else {
        mostrar("Verificando…");
        const imagen = Camara.capturar(video);
        const datos = await Auth.loginFacial(inputIdent.value.trim(), imagen);
        Auth.guardarSesion(
          datos,
          document.getElementById("recordarme").checked,
        );
        Camara.detener(video);
        mostrar("¡Listo! Entrando…", "ok");
        window.location.href = "bienvenida.html";
        return;
      }
    } catch (err) {
      mostrar(err.message, "error");
    } finally {
      ocupado = false;
      btnAccion.disabled = false;
    }
  });
});
