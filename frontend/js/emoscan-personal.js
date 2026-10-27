document.addEventListener('DOMContentLoaded', async () => {
  const $ = (id) => document.getElementById(id);
  const labels = { neutral: 'Neutral', happy: 'Sonrisa', surprise: 'Sorpresa aparente', sad: 'Tristeza aparente', angry: 'Enojo aparente', disgust: 'Disgusto aparente', fear: 'Temor aparente', contempt: 'Desprecio aparente' };
  const base = '/api/emoscan-personal';
  let stream = null, accepted = false, enabled = false, version = null, busy = false, starting = false;
  let generation = 0, pollTimer = null, expiryTimer = null, controller = null, needsDiscard = false;
  let discarding = Promise.resolve();
  const channel = typeof BroadcastChannel === 'undefined' ? null : new BroadcastChannel('emoscan-personal-consent');
  function message(text) { $('emo-status').textContent = text; }
  function error(text = '') { $('emo-error').textContent = text; $('emo-error').hidden = !text; }
  function buttons() {
    $('emo-start').disabled = !enabled || !accepted || !!stream || starting || busy;
    $('emo-analyze').disabled = !enabled || !accepted || !stream || busy;
    $('emo-repeat').disabled = !enabled || !accepted || !stream || busy;
    $('emo-stop').disabled = !stream && !starting;
  }
  async function api(path, options = {}) {
    const r = await Panel.api(base + path, { ...options, cache: 'no-store' });
    const data = r.status === 204 ? {} : await r.json();
    if (!r.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'EmoScan no está disponible.');
    return data;
  }
  function discard() {
    if (!needsDiscard) return discarding;
    needsDiscard = false;
    discarding = api('/jobs', { method: 'DELETE', keepalive: true }).catch(() => {});
    return discarding;
  }
  function clear() {
    generation++; clearTimeout(pollTimer); clearTimeout(expiryTimer); controller?.abort(); controller = null;
    busy = false; $('emo-result').hidden = true; $('emo-label').textContent = ''; $('emo-scores').replaceChildren();
  }
  function stop() {
    clear(); starting = false;
    stream?.getTracks().forEach((track) => track.stop()); stream = null; $('emo-video').srcObject = null;
    discard(); buttons();
  }
  async function loadConsent() {
    try {
      const data = await api('/consent'); accepted = data.accepted; enabled = data.enabled; version = data.text_version;
      $('emo-consent-text').textContent = data.text; $('emo-consent').checked = accepted;
      $('emo-consent').disabled = !enabled; $('emo-revoke').disabled = !accepted;
      message(!enabled ? 'EmoScan está desactivado. Tus otras funciones siguen disponibles.' : accepted ? 'Puedes activar la cámara cuando quieras.' : 'Lee y acepta el consentimiento antes de analizar.');
    } catch (e) { enabled = false; $('emo-consent').disabled = true; error(e.message); message('Consentimiento no disponible. La asistencia no se ve afectada.'); }
    buttons();
  }
  async function updateConsent(value) {
    stop(); error(); accepted = false; buttons(); $('emo-consent').disabled = true; $('emo-revoke').disabled = true;
    try {
      const data = await api('/consent', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ accepted: value, text_version: version }) });
      accepted = data.accepted; $('emo-consent').checked = accepted;
      message(accepted ? 'Consentimiento personal aceptado. Activa la cámara para continuar.' : 'Consentimiento retirado. Cámara detenida y resultados eliminados.');
      channel?.postMessage('changed');
    } catch (e) {
      $('emo-consent').checked = false; error(e.message); message('No se confirmó el cambio. Puedes volver a pulsar Retirar consentimiento.');
    } finally { $('emo-consent').disabled = !enabled; $('emo-revoke').disabled = false; buttons(); }
  }
  $('emo-consent').addEventListener('change', () => void updateConsent($('emo-consent').checked));
  $('emo-revoke').addEventListener('click', () => void updateConsent(false));
  $('emo-start').addEventListener('click', async () => {
    if (!accepted || !enabled || starting || stream) return;
    error(); starting = true; buttons(); const current = generation;
    try {
      if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) throw new Error('La cámara requiere HTTPS o localhost y un navegador compatible.');
      const media = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 640, max: 1280 }, height: { ideal: 480, max: 1280 }, facingMode: 'user' }, audio: false });
      if (current !== generation || !accepted || document.hidden) { media.getTracks().forEach((t) => t.stop()); return; }
      stream = media; $('emo-video').srcObject = stream; await $('emo-video').play();
      if (current === generation) message('Cámara activa. Pulsa Analizar expresión cuando estés listo.');
    } catch (e) { if (current === generation) { stop(); error(e.name === 'NotAllowedError' ? 'Permiso de cámara denegado. Puedes habilitarlo en el navegador e intentarlo de nuevo.' : e.message); } }
    finally { if (current === generation) starting = false; buttons(); }
  });
  $('emo-stop').addEventListener('click', () => { stop(); message('Cámara desactivada.'); });
  function showResult(data, current) {
    if (current !== generation || !accepted) return;
    $('emo-label').textContent = 'Expresión estimada: ' + (labels[data.estimated_expression] || 'No disponible');
    $('emo-scores').replaceChildren();
    for (const [key, label] of Object.entries(labels)) {
      const score = data.scores[key]; if (!Number.isFinite(score) || score < 0 || score > 1) throw new Error('El modelo devolvió puntuaciones inválidas.');
      const row = document.createElement('div'); row.className = 'emo-score';
      const text = document.createElement('span'); text.textContent = label;
      const bar = document.createElement('progress'); bar.max = 1; bar.value = score; bar.setAttribute('aria-label', label);
      const value = document.createElement('span'); value.textContent = (score * 100).toFixed(1) + ' %'; row.append(text, bar, value); $('emo-scores').appendChild(row);
    }
    $('emo-result').hidden = false; message('Análisis completado. Puedes repetirlo voluntariamente.');
    expiryTimer = setTimeout(() => { clear(); discard(); buttons(); message('El resultado temporal ha caducado. Puedes repetir el análisis.'); }, Math.max(0, Math.min(data.expires_in ?? 30, 30)) * 1000);
  }
  async function analyze() {
    if (!stream || !accepted || busy) return;
    clear(); error(); busy = true; buttons(); const current = generation;
    let polling = false;
    controller = new AbortController(); message('Capturando un fotograma y estimando la expresión…');
    try {
      await discard();
      if (current !== generation) return;
      const video = $('emo-video');
      if (!video.videoWidth || !video.videoHeight) throw new Error('Espera a que se muestre la vista previa antes de analizar.');
      const canvas = document.createElement('canvas');
      const scale = Math.min(1, 640 / video.videoWidth, 480 / video.videoHeight);
      canvas.width = Math.round(video.videoWidth * scale); canvas.height = Math.round(video.videoHeight * scale);
      canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', .85));
      canvas.width = 0; canvas.height = 0;
      if (current !== generation || !accepted) return;
      if (!blob) throw new Error('No se pudo capturar la imagen.');
      needsDiscard = true;
      const job = await api('/analizar', { method: 'POST', headers: { 'Content-Type': 'image/jpeg' }, body: blob, signal: controller.signal });
      if (current !== generation) { discard(); return; }
      const deadline = Date.now() + Math.min(job.expires_in ?? 10, 15) * 1000;
      async function poll() {
        if (current !== generation) return;
        let pending = false;
        try {
          if (Date.now() >= deadline) throw new Error('El análisis caducó. Puedes repetirlo.');
          const data = await api('/jobs/' + encodeURIComponent(job.job_id), { signal: controller.signal });
          if (current !== generation) return;
          if (['QUEUED', 'RUNNING'].includes(data.status)) { pending = true; pollTimer = setTimeout(poll, 350); return; }
          if (data.status === 'NO_SINGLE_FACE') throw new Error('Encuadra un único rostro, con buena luz, y repite el análisis.');
          if (data.status !== 'READY') throw new Error('No se pudo analizar la expresión. Puedes repetir el análisis.');
          showResult(data, current);
        } catch (e) { if (current === generation) { error(e.message); message('Análisis no disponible.'); discard(); } }
        finally { if (current === generation && !pending) { busy = false; buttons(); } }
      }
      // La cola mantiene el análisis en RAM y valida de nuevo el consentimiento al consultar.
      polling = true;
      void poll();
    } catch (e) { if (current === generation) { error(e.message); discard(); } }
    finally { if (current === generation && !polling) { busy = false; buttons(); } }
  }
  $('emo-analyze').addEventListener('click', () => void analyze());
  $('emo-repeat').addEventListener('click', () => void analyze());
  window.addEventListener('pagehide', stop);
  window.addEventListener('beforeunload', stop);
  document.addEventListener('visibilitychange', () => { if (document.hidden) { stop(); message('Cámara detenida al salir de la sección.'); } });
  if (channel) channel.onmessage = () => { stop(); void loadConsent(); };
  try { if (!await Panel.iniciar('estudiante')) return; await loadConsent(); }
  catch { error('No se pudo verificar tu sesión. Revisa la conexión con el servidor.'); }
});
