const API_URL = ["localhost", "127.0.0.1"].includes(window.location.hostname)
  ? window.location.protocol + "//" + window.location.hostname + ":8000"
  : "https://monitor-asistencia-ia-production.up.railway.app";
