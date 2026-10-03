document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("form-registro");
  const mensaje = document.getElementById("mensaje");
  const boton = document.getElementById("btn-entrar");
  const inputPass = document.getElementById("password");
  const inputPass2 = document.getElementById("password2");
  const btnOjo = document.getElementById("btn-ojo");

  const bloqueRostro = document.getElementById("bloque-rostro");
  const textoRostro = document.getElementById("texto-rostro");
  const btnRostro = document.getElementById("btn-rostro-registro");
  const modal = document.getElementById("modal-rostro");
  const caja = document.getElementById("caja-video");
  const video = document.getElementById("video-rostro");
  const estado = document.getElementById("estado-rostro");
  const cuenta = document.getElementById("cuenta-atras");
  const consentimiento = document.getElementById("consentimiento");
  const btnAccion = document.getElementById("btn-accion-rostro");
  const btnCerrar = document.getElementById("btn-cerrar-rostro");

  let imagenesRostro = null;
  let paso = "activar";
  let ocupado = false;

  const valor = (id) => document.getElementById(id).value.trim();
  const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

  // ---------- Ver / ocultar contraseñas ----------
  btnOjo.addEventListener("click", () => {
    const oculto = inputPass.type === "password";
    inputPass.type = oculto ? "text" : "password";
    inputPass2.type = oculto ? "text" : "password";
    btnOjo.classList.toggle("activo", oculto);
    btnOjo.setAttribute(
      "aria-label",
      oculto ? "Ocultar contraseñas" : "Mostrar contraseñas",
    );
  });

  // ---------- Validación antes de enviar ----------
  function validar() {
    if (!valor("nombres") || !valor("apellidos"))
      return "Ingresa tus nombres y apellidos.";
    if (!/^[A-Za-z0-9._-]{3,50}$/.test(valor("username"))) {
      return "El usuario debe tener de 3 a 50 caracteres: letras, números, punto, guion o guion bajo.";
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor("email")))
      return "Ingresa un correo válido.";
    const p = inputPass.value;
    if (p.length < 8 || !/[A-Za-z]/.test(p) || !/\d/.test(p)) {
      return "La contraseña debe tener al menos 8 caracteres, con letras y números.";
    }
    if (p !== inputPass2.value) return "Las contraseñas no coinciden.";
    return null;
  }

  function textoDeError(datos) {
    if (typeof datos.detail === "string") return datos.detail;
    if (Array.isArray(datos.detail) && datos.detail[0] && datos.detail[0].msg) {
      return datos.detail[0].msg.replace(/^Value error, /, "");
    }
    return "No se pudo completar el registro. Revisa los datos.";
  }

  // ---------- Envío ----------
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    mensaje.textContent = "";

    const error = validar();
    if (error) {
      mensaje.textContent = error;
      return;
    }

    const cuerpo = {
      username: valor("username"),
      email: valor("email"),
      password: inputPass.value,
      nombres: valor("nombres"),
      apellidos: valor("apellidos"),
      especialidad: valor("especialidad") || null,
    };
    if (imagenesRostro) {
      cuerpo.consentimiento = true;
      cuerpo.imagenes = imagenesRostro;
    }

    boton.disabled = true;
    boton.classList.add("cargando");
    boton.textContent = imagenesRostro
      ? "Verificando tu rostro"
      : "Creando cuenta";

    try {
      const r = await fetch(API_URL + "/api/auth/register-profesor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cuerpo),
      });
      const datos = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(textoDeError(datos));

      document.getElementById("texto-exito").textContent =
        "Un administrador revisará tu cuenta y la activará. " +
        (datos.rostro_registrado
          ? "Tu rostro quedó registrado para entrar con la cámara. "
          : "") +
        "Cuando esté aprobada podrás iniciar sesión.";
      document.getElementById("vista-form").hidden = true;
      document.getElementById("vista-exito").hidden = false;
    } catch (err) {
      mensaje.textContent =
        err instanceof TypeError
          ? "No se pudo conectar con el servidor."
          : err.message;
      boton.disabled = false;
      boton.classList.remove("cargando");
      boton.textContent = "Crear cuenta";
    }
  });

  // ---------- Registro del rostro ----------
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
    mostrar("Necesitamos tu cámara. Tu navegador te pedirá permiso.");
  }

  btnRostro.addEventListener("click", () => {
    pasoInicial();
    modal.showModal();
  });

  btnCerrar.addEventListener("click", () => modal.close());
  modal.addEventListener("close", () => RostroVivo.detener(video));

  async function capturarTres() {
    if (!consentimiento.checked) {
      mostrar("Debes aceptar el consentimiento para continuar.", "error");
      return false;
    }
    const resultados = await RostroVivo.ejecutar(
      [
        { accion: "frente" },
        { accion: "parpadeo" },
        { accion: "giro", dir: "izq" },
      ],
      alEstado,
    );
    imagenesRostro = resultados.map((r) => r.frente);
    return true;
  }

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
          "Acepta el consentimiento y pulsa el botón. Los puntos se ponen verdes cuando estás bien ubicado.",
        );
        btnAccion.textContent = "Iniciar registro de rostro";
        paso = "capturar";
      } else if (await capturarTres()) {
        modal.close();
        bloqueRostro.classList.add("listo");
        textoRostro.textContent =
          "Rostro capturado. Se guardará al crear tu cuenta.";
        btnRostro.textContent = "Volver a capturar";
      }
    } catch (err) {
      if (err.message !== "cancelado") mostrar(err.message, "error");
    } finally {
      ocupado = false;
      btnAccion.disabled = false;
    }
  });
});
