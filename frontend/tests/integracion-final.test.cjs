/* Browser QA: node frontend/tests/integracion-final.test.cjs
   Set SEGMENTATION_FIXTURE to JSON computed by the real Python model.
   PLAYWRIGHT_MODULE and CHROME_EXECUTABLE are optional overrides for local tooling.
   Personal expression replies and the camera are synthetic test doubles. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const fixture = JSON.parse(fs.readFileSync(process.env.SEGMENTATION_FIXTURE || path.resolve(root, '../segmentacion/.cache/demo_api.json'), 'utf8'));
const smallFixture = JSON.parse(fs.readFileSync(process.env.SEGMENTATION_SMALL_FIXTURE || path.resolve(root, '../segmentacion/.cache/demo_api_small.json'), 'utf8'));
const legacyFixture = JSON.parse(fs.readFileSync(process.env.SEGMENTATION_LEGACY_FIXTURE || path.resolve(root, '../segmentacion/.cache/demo_api_legacy.json'), 'utf8'));
const sample = fs.readFileSync(path.join(root, 'ejemplos/segmentacion_sintetica.csv'));
let checks = 0;
const check = (condition, message) => { assert.ok(condition, message); checks++; };
const server = http.createServer((req, res) => {
  const name = path.resolve(root, '.' + decodeURIComponent(new URL(req.url, 'http://localhost').pathname));
  if (!name.startsWith(root + path.sep)) { res.writeHead(403); res.end(); return; }
  fs.readFile(name, (err, body) => {
    if (err) { res.writeHead(404); res.end(); return; }
    const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png', '.csv': 'text/csv' };
    res.writeHead(200, { 'Content-Type': mime[path.extname(name)] || 'application/octet-stream' }); res.end(body);
  });
});

(async () => {
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const url = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch({ headless: true,
    ...(process.env.CHROME_EXECUTABLE ? { executablePath: process.env.CHROME_EXECUTABLE } : {}),
    args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] });
  const contexts = [];
  async function setup(role) {
    const context = await browser.newContext({ permissions: ['camera'], acceptDownloads: true }); contexts.push(context);
    await context.addInitScript(() => { localStorage.setItem('token', 'synthetic-browser-test'); });
    if (role === 'estudiante') await context.addInitScript(() => {
      // Canvas frames avoid reliance on a physical or OS-level camera device.
      Object.defineProperty(navigator.mediaDevices, 'getUserMedia', { configurable: true, value: async () => {
        const canvas = document.createElement('canvas'); canvas.width = 640; canvas.height = 480;
        const context = canvas.getContext('2d');
        const stream = canvas.captureStream(10);
        const timer = setInterval(() => {
          if (!stream.getVideoTracks().some((t) => t.readyState === 'live')) { clearInterval(timer); return; }
          context.fillStyle = '#2563eb'; context.fillRect(0, 0, 640, 480);
        }, 60);
        return stream;
      } });
    });
    const state = { accepted: false, posts: [], analyses: 0, polls: 0, delayed: false };
    await context.route('https://fonts.googleapis.com/**', (r) => r.abort());
    await context.route('http://127.0.0.1:8000/**', async (route) => {
      const req = route.request(), p = new URL(req.url()).pathname;
      const reply = (data, status = 200) => route.fulfill({ status, json: data, headers: { 'Access-Control-Allow-Origin': '*' } });
      state.posts.push({ method: req.method(), path: p });
      if (p === '/api/users/me') return reply({ id: 1, rol: role, nombres: 'Cuenta', apellidos: 'Sintética' });
      if (p.startsWith('/api/segmentacion/')) {
        if (req.method() === 'POST' && req.postData().includes(',real')) return reply({ detail: 'Cada fila debe declarar origen_datos=sintetico.' }, 422);
        if (state.badResponse) { const bad = JSON.parse(JSON.stringify(fixture)); bad.puntos[0].asistencia_ratio = 2; return reply(bad); }
        if (state.override) return reply(state.override);
        return reply(req.headers()['x-csv-filename'] === 'pequeno.csv' ? smallFixture : req.method()==='POST'&&!req.headers()['x-csv-filename']?.includes('categorias') ? legacyFixture : fixture);
      }
      if (p.endsWith('/consent')) {
        if (req.method() === 'PUT') state.accepted = req.postDataJSON().accepted;
        return reply({ accepted: state.accepted, enabled: true, text_version: 'test-personal-v1', text: 'Consentimiento personal de prueba. No registra asistencia.' });
      }
      if (p.endsWith('/analizar')) { state.analyses++; return reply({ status: 'QUEUED', job_id: 'synthetic-job', expires_in: 10 }, 202); }
      if (p.endsWith('/jobs') && req.method() === 'DELETE') return route.fulfill({ status: 204 });
      if (p.includes('/jobs/')) {
        state.polls++;
        if (state.delayed) await new Promise((r) => setTimeout(r, 500));
        return reply({ status: 'READY', estimated_expression: 'neutral', scores: Object.fromEntries(['neutral','happy','surprise','sad','angry','disgust','fear','contempt'].map((k) => [k, .125])), expires_in: 30 });
      }
      return reply({ detail: 'Unexpected test endpoint' }, 404);
    });
    const page = await context.newPage();
    const errors = []; page.on('pageerror', (error) => errors.push(error.message));
    return { context, page, state, errors };
  }
  try {
    const teacher = await setup('profesor'), p = teacher.page;
    await p.goto(url + '/profesor/segmentacion.html');
    await p.locator('.admin-menu a[href="segmentacion.html"]').waitFor();
    await require('./segmentacion-dashboard.checks.cjs')(teacher, url, fixture, sample, check, smallFixture);

    const student = await setup('estudiante'), e = student.page;
    await e.goto(url + '/estudiante/emoscan.html'); await e.locator('.admin-menu a[href="emoscan.html"]').waitFor();
    check(await e.locator('.admin-menu').innerText().then((x) => x.includes('EmoScan') && !x.includes('Segmentación IA')), 'Student has personal EmoScan only');
    check(await e.locator('#emo-start').isDisabled(), 'Camera requires explicit personal consent');
    await e.locator('#emo-consent').check(); await e.waitForFunction(() => !document.getElementById('emo-start').disabled);
    await e.locator('#emo-start').click(); await e.waitForFunction(() => document.getElementById('emo-video').videoWidth > 0);
    check(student.state.analyses === 0, 'Preview does not automatically analyze');
    await e.locator('#emo-analyze').click(); await e.locator('#emo-result').waitFor({ state: 'visible' });
    check(await e.locator('#emo-scores progress').count() === 8, 'Eight FERPlus score bars');
    await e.locator('#emo-repeat').click(); await e.waitForFunction(() => !document.getElementById('emo-result').hidden);
    check(student.state.analyses === 2, 'Repeat submits another independent analysis');
    check(student.state.posts.every((x) => !x.path.includes('/attendance/')), 'Personal screen never registers attendance');
    student.state.delayed = true;
    await e.locator('#emo-repeat').click(); await e.locator('#emo-revoke').click();
    await e.waitForFunction(() => !document.getElementById('emo-consent').checked);
    await e.waitForTimeout(650);
    check(await e.locator('#emo-result').isHidden(), 'Revocation discards delayed results');
    check(await e.evaluate(() => document.getElementById('emo-video').srcObject === null), 'Revocation stops camera');
    await e.bringToFront();
    await e.locator('#emo-consent').check(); await e.waitForFunction(() => !document.getElementById('emo-start').disabled);
    await e.locator('#emo-start').click();
    try { await e.waitForFunction(() => document.getElementById('emo-video').srcObject !== null); }
    catch (error) { throw new Error(error.message + '\nCamera state: ' + await e.locator('#emo-status').innerText() + ' / ' + await e.locator('#emo-error').textContent()); }
    await e.evaluate(() => window.dispatchEvent(new PageTransitionEvent('pagehide')));
    check(await e.evaluate(() => document.getElementById('emo-video').srcObject === null), 'Leaving stops tracks and preview');
    await e.setViewportSize({ width: 390, height: 844 });
    const mobile = await e.evaluate(() => ({ width: window.innerWidth, scroll: document.documentElement.scrollWidth,
      overflow: [...document.querySelectorAll('body *')].filter((el) => el.getBoundingClientRect().right > innerWidth + 2).map((el) => el.tagName + '#' + el.id + '.' + el.className).slice(0, 12) }));
    check(mobile.scroll <= mobile.width + 2, 'Personal screen fits mobile viewport: ' + JSON.stringify(mobile));
    await e.evaluate(() => Object.defineProperty(navigator.mediaDevices, 'getUserMedia', { value: async () => { throw new DOMException('Permission denied', 'NotAllowedError'); } }));
    await e.locator('#emo-start').click();
    await e.waitForFunction(() => document.getElementById('emo-error').textContent.includes('Permiso de cámara denegado'));
    check(await e.evaluate(() => document.getElementById('emo-video').srcObject === null), 'Camera denial remains recoverable and does not retain tracks');
    // Test frontend role redirects separately from backend role tests.
    const wrong = await setup('estudiante'); await wrong.page.goto(url + '/profesor/segmentacion.html');
    await wrong.page.waitForURL('**/estudiante/cursos.html');
    check(true, 'Frontend rejects student on professor page');
    const admin = await setup('admin'); await admin.page.goto(url + '/estudiante/emoscan.html');
    await admin.page.waitForURL('**/admin/usuarios.html');
    check(true, 'Frontend redirects administrator to existing admin functions');
    check(teacher.errors.length === 0 && student.errors.length === 0, 'No uncaught JavaScript errors on new pages');
    console.log(`OK: ${checks} browser assertions; real computed K-Means fixture, synthetic camera and personal inference replies.`);
  } finally { await Promise.all(contexts.map((c) => c.close())); await browser.close(); }
})().catch((error) => { console.error(error); process.exitCode = 1; }).finally(() => server.close());
