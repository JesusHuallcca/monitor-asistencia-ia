// Extiende Auth con el login facial
Auth.loginFacial = async function (identificador, imagen) {
  let respuesta;
  try {
    respuesta = await fetch(API_URL + "/api/auth/face-login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identificador, imagen }),
    });
  } catch (e) {
    throw new Error("No se pudo conectar con el servidor.");
  }
  const datos = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    throw new Error(
      typeof datos.detail === "string"
        ? datos.detail
        : "No se pudo verificar tu identidad.",
    );
  }
  return datos;
};
