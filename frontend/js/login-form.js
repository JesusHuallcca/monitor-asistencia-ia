document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("form-login");
  const mensaje = document.getElementById("mensaje");
  const boton = document.getElementById("btn-entrar");
  const inputPass = document.getElementById("password");
  const btnOjo = document.getElementById("btn-ojo");
  const textoOriginal = boton.textContent;

  btnOjo.addEventListener("click", () => {
    const oculto = inputPass.type === "password";
    inputPass.type = oculto ? "text" : "password";
    btnOjo.classList.toggle("activo", oculto);
    btnOjo.setAttribute(
      "aria-label",
      oculto ? "Ocultar contraseña" : "Mostrar contraseña",
    );
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    mensaje.textContent = "";
    mensaje.classList.remove("info");

    const identificador = document.getElementById("identificador").value.trim();
    if (!identificador || !inputPass.value) {
      mensaje.textContent = "Ingresa tu usuario y tu contraseña.";
      return;
    }

    boton.disabled = true;
    boton.classList.add("cargando");
    boton.textContent = "Ingresando";

    try {
      const recordarme = document.getElementById("recordarme").checked;
      const datos = await Auth.login(
        form.dataset.endpoint,
        identificador,
        inputPass.value,
        recordarme,
      );
      Auth.guardarSesion(datos, recordarme);
      window.location.href = form.dataset.destino;
    } catch (err) {
      mensaje.textContent = err.message;
      mensaje.classList.toggle("info", err.status === 403); // cuenta en revisión: aviso, no error
      boton.disabled = false;
      boton.classList.remove("cargando");
      boton.textContent = textoOriginal;
      inputPass.focus();
    }
  });
});
