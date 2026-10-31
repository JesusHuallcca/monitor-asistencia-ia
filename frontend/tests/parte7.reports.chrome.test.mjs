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
const downloads=await fs.mkdtemp(path.join(os.tmpdir(),'parte7-reportes-chrome-'));
let checks=0;let teacherReport,teacherFile;
function check(value,message){assert(value,message);checks++;}
async function question(page,text){
 await page.locator('#chat-input').fill(text);
 const pending=page.waitForResponse(r=>r.url().endsWith('/api/chatbot/message')&&r.request().method()==='POST');
 await page.locator('#chat-input').press('Enter');const response=await pending;
 assert.equal(response.status(),200,await response.text());const data=await response.json();
 await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled);
 return data;
}
try{
 for(const viewport of [{width:1366,height:768},{width:1920,height:1080},{width:390,height:844}]){
  const context=await browser.newContext({viewport,acceptDownloads:true});
  await context.addInitScript(()=>{
   class Recognition{constructor(){window.__reportRecognition=this;}start(){this.onstart?.();}abort(){this.onend?.();}result(text){const row=[{transcript:text}];row.isFinal=true;this.onresult({results:[row]});this.onend();}}
   Object.defineProperty(window,'SpeechRecognition',{value:Recognition,configurable:true});
  });
  const page=await context.newPage(),errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto(origin);await page.getByRole('button',{name:'Probar como profesor'}).click();await page.waitForURL('**/frontend/profesor/ia.html');
  await page.locator('#chat-panel').waitFor({state:'attached'});if(await page.locator('#chat-panel').isHidden())await page.locator('#chat-launch').click();await page.locator('#chat-course').selectOption('2');
  const first=await question(page,'Genera el reporte de asistencia de mi curso de octubre');
  check(first.report.report_rows===4,'Cuatro registros de octubre reales');
  check(first.report.metrics.asistencia_pct===100,'Porcentaje calculado');
  const card=page.locator('.chat-report').last();
  check(await card.locator('table').count()===1,'Vista previa tabular');
  check(await card.locator('meter').count()===3,'Barras de estados');
  check((await card.innerText()).includes('Programación'),'Curso en la vista previa');
  check(await card.getByRole('button',{name:'Descargar Excel'}).isVisible(),'Botones reales tras vista previa');
  if(viewport.width===1366){
   teacherReport=first.report.id;
   for(const [fmt,label] of [['xlsx','Descargar Excel'],['pdf','Descargar PDF'],['docx','Descargar Word']]){
    const pending=page.waitForEvent('download');await card.getByRole('button',{name:label,exact:true}).click();const file=await pending;
    check(file.suggestedFilename().endsWith('.'+fmt),'Nombre del formato '+fmt);
    const target=path.join(downloads,file.suggestedFilename());await file.saveAs(target);const bytes=await fs.readFile(target);
    check(bytes.length>1000,'Archivo real '+fmt);check(bytes.subarray(0,2).toString()===(fmt==='pdf'?'%P':'PK'),'Firma '+fmt);
   }
   teacherFile='/api/chatbot/reports/'+teacherReport+'/files/pdf';
   const popupPromise=page.waitForEvent('popup');await card.getByRole('button',{name:'Imprimir PDF',exact:true}).click();const popup=await popupPromise;
   await popup.waitForURL(url=>url.protocol==='blob:',{timeout:20000});check(popup.url().startsWith('blob:'),'PDF autenticado abierto para impresión');await popup.close();
   let same=await question(page,'Ahora quiero el mismo reporte en PDF');check(same.report.id===first.report.id&&same.report.fingerprint===first.report.fingerprint,'Seguimiento conserva dataset');
   same=await question(page,'Descárgalo en Word');check(same.report.requested_formats[0]==='docx','Word reconocido');
   const comparison=await question(page,'Compara la asistencia de septiembre y octubre');
   check(comparison.report.comparison[0].asistencia_pct===75&&comparison.report.comparison[1].asistencia_pct===100,'Comparación real de períodos');
   check(comparison.report.comparison_delta_pp===25,'Diferencia de 25 puntos porcentuales');
   // Mismo endpoint desde transcripción simulada, sin acceder al micrófono físico.
   await page.locator('#chat-mic').click();await page.locator('#chat-mic-allow').click();
   const pending=page.waitForResponse(r=>r.url().endsWith('/api/chatbot/message')&&r.request().method()==='POST');
   await page.evaluate(()=>window.__reportRecognition.result('Genera el reporte de faltas de mis estudiantes'));
   const voiceResponse=await pending;check(voiceResponse.request().postDataJSON().source==='voice','Solicitud hablada usa texto transcrito');
   const voice=await voiceResponse.json();check(voice.report.spec.report_type==='ausencias','Reporte por voz');
   await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled);
   const empty=await question(page,'Genera reporte de asistencia de enero de 2020');
   check(empty.report.chart.length===0&&empty.report.message==='Sin datos disponibles','Sin gráfico falso cuando no hay datos');
   check(await page.locator('.chat-report').last().locator('.chat-report-chart').count()===0,'Gráfico vacío omitido');
   // Volver a una vista previa con datos para la evidencia.
   await question(page,'Genera reporte de asistencia de octubre');
  }
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Sin desbordamiento horizontal');
  check(errors.length===0,'Sin errores JavaScript: '+errors.join(';'));
  await page.locator('.chat-report').last().locator('h3').scrollIntoViewIfNeeded();await page.waitForTimeout(250);
  await page.screenshot({path:path.join(evidence,`reportes-${viewport.width}.png`),fullPage:true});
  await context.close();
 }
 const context=await browser.newContext(),page=await context.newPage();await page.goto(origin);await page.getByRole('button',{name:'Probar como estudiante'}).click();await page.waitForURL('**/frontend/estudiante/ia.html');await page.locator('#chat-panel').waitFor({state:'attached'});if(await page.locator('#chat-panel').isHidden())await page.locator('#chat-launch').click();
 const student=await question(page,'Descarga mi historial de asistencia');check(student.report.rows.every(row=>row.estudiante==='Ana Sintético'),'Reporte del estudiante solo propio');
 const unauthorized=await page.evaluate(async url=>{const response=await Auth.fetchAutenticado(url);return response.status;},teacherFile);check(unauthorized===404,'Archivo del profesor inaccesible al estudiante');
 await context.close();
 console.log(`OK: ${checks} comprobaciones de reportes en Chrome real: vista previa, tres descargas, PDF imprimible, voz transcrita simulada, períodos, datos vacíos, roles y responsive. Descargas de prueba: ${downloads}`);
}finally{await browser.close();}
