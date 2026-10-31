// Inicializador estándar del módulo Red Neuronal IA para el Panel del Profesor (SENATI)
(function initPanelProfesorRedNeuronal() {
  function enlazarLogout() {
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
  }

  async function montar() {
    try {
      enlazarLogout();
      if (window.Panel) {
        await Panel.iniciar("profesor");
      }
    } catch (e) {
      console.error("Error al inicializar Panel en Red Neuronal:", e);
    }
  }

  enlazarLogout();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", montar);
  } else {
    montar();
  }
})();
