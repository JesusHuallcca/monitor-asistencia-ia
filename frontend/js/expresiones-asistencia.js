/* Uses the Monitor's existing authenticated transport; never captures a frame. */
(() => {
    const base = API_URL.replace(/\/api\/attendance\/camera\/check-in$/, "/api/expressions");
    const consent = document.getElementById("expressionConsent");
    const revoke = document.getElementById("expressionRevoke");
    const text = document.getElementById("expressionConsentText");
    const output = document.getElementById("expressionResult");
    let version = null;
    let generation = 0;
    let timer = null;
    let expiry = null;
    const channel = typeof BroadcastChannel === "undefined" ? null : new BroadcastChannel("emoscan-consent");
    const labels = {
        happy: "sonrisa (happy)", neutral: "neutral", surprise: "sorpresa aparente",
        sad: "tristeza aparente", angry: "enojo aparente", disgust: "disgusto aparente",
        fear: "temor aparente", contempt: "desprecio aparente",
    };

    async function api(path, options = {}) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 3000);
        try {
            const response = await fetchConToken(base + path, {
                ...options, cache: "no-store", signal: controller.signal,
            });
            if (!response.ok) throw new Error("Análisis opcional no disponible");
            return await response.json();
        } finally { clearTimeout(timeout); }
    }

    function clear() {
        generation += 1;
        clearTimeout(timer);
        clearTimeout(expiry);
        output.textContent = "";
    }

    async function load() {
        try {
            const data = await api("/consent");
            version = data.text_version;
            text.textContent = data.text;
            consent.checked = data.accepted;
            consent.disabled = !data.enabled;
            revoke.disabled = !data.accepted;
            if (!data.enabled) output.textContent = "Análisis opcional desactivado; la asistencia continúa disponible.";
        } catch (_) {
            consent.disabled = true;
            output.textContent = "Análisis opcional no disponible; la asistencia continúa disponible.";
        }
    }

    async function update(accepted) {
        clear();
        consent.disabled = true;
        revoke.disabled = true;
        try {
            const data = await api("/consent", {
                method: "PUT", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ accepted, text_version: version }),
            });
            consent.checked = data.accepted;
            output.textContent = data.accepted ? "Permiso activado para próximas asistencias." : "Permiso revocado.";
            channel?.postMessage("changed");
        } catch (_) {
            consent.checked = false;
            output.textContent = "No se pudo confirmar el cambio de permiso. Puedes reintentar revocarlo; la asistencia no se ve afectada.";
        } finally {
            consent.disabled = false;
            revoke.disabled = false; // Allow retry even if a network response was lost.
        }
    }

    consent.addEventListener("change", () => update(consent.checked));
    revoke.addEventListener("click", () => update(false));
    window.addEventListener("pagehide", clear);
    document.addEventListener("visibilitychange", () => {
        if (document.hidden) clear();
    });
    if (channel) channel.onmessage = () => { clear(); void load(); };

    window.EmoScanAttendance = {
        follow(analysis) {
            clear();
            if (!analysis || analysis.status === "DISABLED" || analysis.status === "NO_CONSENT") return;
            if (analysis.status !== "QUEUED") {
                output.textContent = "Asistencia confirmada. Análisis de expresiones no disponible.";
                return;
            }
            const current = generation;
            const deadline = Date.now() + Math.min(analysis.expires_in, 15) * 1000;
            output.textContent = "Asistencia confirmada. Estimando expresión facial…";
            async function poll() {
                if (current !== generation) return;
                if (Date.now() >= deadline) {
                    output.textContent = "Asistencia confirmada. Análisis no disponible o caducado.";
                    return;
                }
                try {
                    const data = await api("/jobs/" + encodeURIComponent(analysis.job_id));
                    if (current !== generation) return;
                    if (data.status === "QUEUED" || data.status === "RUNNING") {
                        timer = setTimeout(poll, 500);
                    } else if (data.status === "READY") {
                        const score = data.scores[data.estimated_expression];
                        output.textContent = `Expresión facial estimada: ${labels[data.estimated_expression] || data.estimated_expression}. Puntuación del modelo: ${(score * 100).toFixed(2)} %. No demuestra emociones internas, atención ni rendimiento.`;
                        expiry = setTimeout(clear, Math.min(data.expires_in ?? 30, 30) * 1000);
                    } else {
                        output.textContent = "Asistencia confirmada. Análisis de expresiones no disponible.";
                    }
                } catch (_) {
                    if (current === generation) output.textContent = "Asistencia confirmada. Análisis no disponible o caducado.";
                }
            }
            void poll();
        },
    };
    void load();
})();
