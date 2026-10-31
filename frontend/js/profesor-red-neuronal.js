// Inicializador estándar del módulo Red Neuronal IA para el Panel del Profesor (SENATI)
(function initPanelProfesorRedNeuronal() {
  function enlazarControles() {
    const btn = document.getElementById("menu-btn-salir");
    if (btn && !btn._bound) {
      btn._bound = true;
      btn.addEventListener("click", () => {
        if (window.Auth) Auth.limpiar();
        window.location.href = "../login.html";
      });
    }
    const nom = (window.Auth && Auth.leer("nombre")) || "Carlos Ramírez";
    const elNom = document.getElementById("menu-profesor-nombre");
    if (elNom) elNom.textContent = nom;

    const btnCerrar = document.querySelector(".btn-cerrar-drawer");
    if (btnCerrar && !btnCerrar._bound) {
      btnCerrar._bound = true;
      btnCerrar.addEventListener("click", () => {
        if (window.Panel) Panel.cerrarMenuMovil();
      });
    }
  }

  async function montar() {
    try {
      enlazarControles();
      if (window.Panel) {
        await Panel.iniciar("profesor");
      }
      enlazarControles();
    } catch (e) {
      console.error("Error al inicializar Panel en Red Neuronal:", e);
    }
  }

  enlazarControles();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", montar);
  } else {
    montar();
  }
})();
