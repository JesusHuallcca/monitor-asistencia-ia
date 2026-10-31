import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {tool} from './parte7-tools.mjs';
const {chromium}=await tool('playwright');
const origin=process.env.MONITOR_LIVE_DEMO_URL||'http://127.0.0.1:8017';
assert(['127.0.0.1','localhost'].includes(new URL(origin).hostname));
const health=await(await fetch(origin+'/api/health')).json();assert(health.demo&&health.mysql==='blocked'&&health.storage==='sqlite-memory');
const browser=await chromium.launch({channel:'chrome',headless:true});
const evidence=path.resolve(fileURLToPath(new URL('../../docs/parte7/evidencias',import.meta.url)));
const downloads=await fs.mkdtemp(path.join(os.tmpdir(),'parte7-ml-chrome-'));
let checks=0;
function check(value,label){assert(value,label);checks++;}
async function ask(page,text){
 await page.locator('#chat-input').fill(text);
 const pending=page.waitForResponse(r=>r.url().endsWith('/api/chatbot/message')&&r.request().method()==='POST');
 await page.locator('#chat-input').press('Enter');const response=await pending;
 assert.equal(response.status(),200,await response.text());const data=await response.json();
 await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled);
 return data;
}
try{
 for(const viewport of [{width:1366,height:768},{width:1920,height:1080},{width:390,height:844}]){
  const context=await browser.newContext({viewport,acceptDownloads:true});const page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(origin);await page.getByRole('button',{name:'Probar como profesor'}).click();await page.waitForURL('**/frontend/profesor/ia.html');await page.locator('#chat-panel').waitFor({state:'attached'});if(await page.locator('#chat-panel').isHidden())await page.locator('#chat-launch').click();
  let data=await ask(page,'¿Qué es K-Means?');check(data.intent==='ML_EXPLAIN','Explicación educativa');
  data=await ask(page,'Muestra resultados K-Means sintéticos');
  check(data.ml.profiles===150&&data.ml.k===3,'150 perfiles K=3 guardados');
  check(Math.abs(data.ml.metrics.silueta-.2373692496101911)<1e-10,'Silueta original');
  let card=page.locator('.chat-ml').last();check((await card.innerText()).includes('Datos sintéticos'),'Procedencia visible');
  await card.locator('summary').click();check((await card.innerText()).includes('expresiones_positivas_ratio'),'Cuatro variables sin usar datos faciales');
  data=await ask(page,'Consulta la probabilidad de asistencia con Parte 6');
  check(data.ml.status==='pending'&&!('probability' in data.ml),'Parte 6 pendiente honesta');
  check((await page.locator('.chat-ml').last().innerText()).includes('Pendiente'),'Tarjeta de servicio pendiente');
  data=await ask(page,'¿Y qué variables utiliza?');check(data.intent==='ML_EXPLAIN'&&data.reply.includes('asistencia_30d'),'Seguimiento conserva variables de Parte 6');
  data=await ask(page,'¿Y mi probabilidad?');check(data.intent==='ML_NEURAL'&&data.ml.status==='pending','Seguimiento no cambia de predictor ni inventa probabilidad');
  data=await ask(page,'Genera reporte de evaluación y comparación de regresión y K-Means');
  check(data.report.kind==='ml_evaluation'&&!data.report.comparable&&data.report.winner===null,'Sin ganador inventado');
  const report=page.locator('.chat-report').last();check(await report.locator('table').count()===1,'Tabla real de evaluación');
  check((await report.innerText()).includes('no_verificado'),'Origen no acreditado declarado');
  check(!(await report.innerText()).includes('undefined'),'Sin valores indefinidos');
  check(!(await report.innerText()).includes('Registros base'),'No se confunden métricas ML con asistencias');
  if(viewport.width===1366){
   for(const [fmt,label] of [['xlsx','Descargar Excel'],['pdf','Descargar PDF'],['docx','Descargar Word']]){
    await report.getByRole('button',{name:label,exact:true}).scrollIntoViewIfNeeded();
    const pending=page.waitForEvent('download');await report.getByRole('button',{name:label,exact:true}).click();const file=await pending;
    const target=path.join(downloads,file.suggestedFilename());await file.saveAs(target);const bytes=await fs.readFile(target);
    check(bytes.length>1000&&bytes.subarray(0,2).toString()===(fmt==='pdf'?'%P':'PK'),'Descarga '+fmt+' real');
   }
  }
  data=await ask(page,'Ahora quiero el mismo reporte en PDF');check(data.report.requested_formats.includes('pdf'),'Seguimiento de formato');
  check(data.report.kind==='ml_evaluation','Seguimiento conserva tipo ML');
  await page.locator('.chat-report').last().scrollIntoViewIfNeeded();
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Sin desbordamiento horizontal');
  await page.screenshot({path:path.join(evidence,'ml-'+viewport.width+'.png'),fullPage:true});
  check(errors.length===0,'Sin errores JavaScript');
  await context.close();
 }
 const context=await browser.newContext();const page=await context.newPage();
 await page.goto(origin);await page.getByRole('button',{name:'Probar como estudiante'}).click();await page.waitForURL('**/frontend/estudiante/ia.html');await page.locator('#chat-panel').waitFor({state:'attached'});if(await page.locator('#chat-panel').isHidden())await page.locator('#chat-launch').click();
 const explanation=await ask(page,'Diferencias entre regresión y red neuronal');check(explanation.intent==='ML_EXPLAIN','Estudiante accede a explicaciones');
 const mine=await ask(page,'Mi cluster K-Means');check(mine.ml.status==='pending'&&!mine.ml.groups,'No asigna perfiles sintéticos a estudiantes');
 check(await page.evaluate(async()=>{const response=await Auth.fetchAutenticado('/api/chatbot/ml/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model:'red_neuronal_parte6',operation:'predict',course_id:1,student_id:1})});return response.status;})===403,'Contrato profesor no permite inferencia neuronal estudiantil');
 await context.close();
 console.log('OK: '+checks+' comprobaciones Chrome + FastAPI + JWT + SQLite reales; ML, permisos, estados pendientes, tres descargas y tres resoluciones. Sin entrenamiento ni MySQL.');
}finally{await browser.close();}
