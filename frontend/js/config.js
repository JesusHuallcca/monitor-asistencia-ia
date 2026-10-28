const API_URL = window.localStorage.getItem("API_URL") || (
  ["localhost", "127.0.0.1"].includes(window.location.hostname)
    ? window.location.protocol + "//" + window.location.hostname + ":8000"
    : window.location.hostname.includes("onrender.com")
    ? "https://monitor-asistencia-backend.onrender.com"
    : "https://monitor-asistencia-ia-production.up.railway.app"
);
