/* Dependency-free JS tests. Run: node frontend/tests/emoscan.test.js */
async function runEmoScanTests(cameraSource, expressionsSource) {
    let assertions = 0;
    function check(value, message) {
        if (!value) throw new Error(message);
        assertions += 1;
    }
    const flush = async () => { for (let i = 0; i < 30; i += 1) await Promise.resolve(); };

    async function setup() {
        const elements = {};
        for (const id of ["expressionConsent", "expressionRevoke", "expressionConsentText", "expressionResult"]) {
            elements[id] = { textContent: "", checked: false, disabled: false, listeners: {},
                addEventListener(event, callback) { this.listeners[event] = callback; } };
        }
        const timers = new Map();
        let timerId = 0;
        const calls = [];
        let jobReply = { status: "RUNNING" };
        let jobResolver = null;
        let delayed = false;
        const window = { addEventListener() {} };
        const document = { hidden: false, listeners: {},
            getElementById: id => elements[id],
            addEventListener(event, callback) { this.listeners[event] = callback; } };
        const transport = async (url, options) => {
            calls.push({ url, options });
            if (url.endsWith("/consent")) {
                return { ok: true, json: async () => options.method === "PUT"
                    ? { accepted: JSON.parse(options.body).accepted }
                    : { accepted: false, text_version: "test-v1", text: "Consentimiento específico", enabled: true } };
            }
            if (delayed) await new Promise(resolve => { jobResolver = resolve; });
            return { ok: true, json: async () => jobReply };
        };
        new Function("window", "document", "API_URL", "fetchConToken", "setTimeout", "clearTimeout", "AbortController", "BroadcastChannel", expressionsSource)(
            window, document, "http://test/api/attendance/camera/check-in", transport,
            (fn, ms) => { const id = ++timerId; timers.set(id, { fn, ms }); return id; },
            id => timers.delete(id), class { signal = {}; abort() {} }, undefined);
        await flush();
        return { window, document, elements, calls, timers,
            setReply(value) { jobReply = value; },
            delay() { delayed = true; }, resolve() { jobResolver(); }, flush };
    }

    let env = await setup();
    check(!env.elements.expressionConsent.checked, "Consent must start unchecked");
    check(env.elements.expressionConsentText.textContent === "Consentimiento específico", "Show server consent text");
    env.elements.expressionConsent.checked = true;
    env.elements.expressionConsent.listeners.change();
    await flush();
    check(JSON.parse(env.calls.at(-1).options.body).accepted === true, "Explicit acceptance is sent");
    check(env.calls.every(call => call.options.cache === "no-store"), "Do not cache results");

    env.setReply({ status: "READY", estimated_expression: "happy", scores: { happy: .9 }, expires_in: 4 });
    env.window.EmoScanAttendance.follow({ status: "QUEUED", job_id: "test", expires_in: 10 });
    await flush();
    check(env.elements.expressionResult.textContent.includes("Expresión facial estimada"), "Label as estimate");
    check(env.elements.expressionResult.textContent.includes("No demuestra emociones internas"), "Explain scope");
    const expiration = [...env.timers.values()].find(timer => timer.ms === 4000);
    check(Boolean(expiration), "Clear result on server expiry");
    expiration.fn();
    check(env.elements.expressionResult.textContent === "", "Expired result is removed");

    env = await setup();
    env.delay();
    env.window.EmoScanAttendance.follow({ status: "QUEUED", job_id: "pending", expires_in: 10 });
    await flush();
    env.elements.expressionRevoke.listeners.click();
    await flush();
    check(JSON.parse(env.calls.at(-1).options.body).accepted === false, "Revocation is sent");
    env.setReply({ status: "READY", estimated_expression: "happy", scores: { happy: .9 } });
    env.resolve();
    await flush();
    check(env.elements.expressionResult.textContent === "Permiso revocado.", "Late result cannot overwrite revocation");
    env.document.hidden = true;
    env.document.listeners.visibilitychange();
    check(env.elements.expressionResult.textContent === "", "Hide clears sensitive output");

    // Exercise the existing camera class: registration callback precedes optional analysis.
    const order = [];
    const w = { EmoScanAttendance: { follow() { order.push("analysis"); throw new Error("optional failure"); } } };
    new Function("window", cameraSource)(w);
    const camera = new w.AttendanceCamera({}, { onSuccess() { order.push("attendance"); } });
    camera.handleResponse({ status: "REGISTERED", expression_analysis: { status: "QUEUED" } });
    check(order.join(",") === "attendance,analysis", "Attendance succeeds before optional UI error");
    check(camera.running === false, "Existing attendance camera pauses");
    check(!/getUserMedia|VideoCapture|toDataURL/.test(expressionsSource), "Expressions UI never opens or captures camera");
    return { assertions, status: "OK" };
}

if (typeof module !== "undefined" && typeof require !== "undefined") {
    const fs = require("node:fs");
    const path = require("node:path");
    runEmoScanTests(
        fs.readFileSync(path.join(__dirname, "../components/camera.js"), "utf8"),
        fs.readFileSync(path.join(__dirname, "../js/expresiones-asistencia.js"), "utf8"),
    ).then(result => console.log(result)).catch(error => { console.error(error); process.exitCode = 1; });
}
