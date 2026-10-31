/* Evidencia integrada: solo la demo local con SQLite RAM y MySQL bloqueado. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {tool} from './parte7-tools.mjs';
const {chromium}=await tool('playwright');
const origin=process.env.MONITOR_LIVE_DEMO_URL||'http://127.0.0.1:8017';
assert(['127.0.0.1','localhost'].includes(new URL(origin).hostname));
const health=await(await fetch(origin+'/api/health')).json();
assert(health.demo&&health.mysql==='blocked'&&health.storage==='sqlite-memory');
const target=path.resolve(fileURLToPath(new URL('../../docs/parte7/evidencias',import.meta.url)));
const browser=await chromium.launch({channel:'chrome',headless:true});let checks=0;
function check(condition,label){assert(condition,label);checks++;}
try{
 for(const [role,viewport] of [['profesor',{width:1920,height:1080}],['profesor',{width:1366,height:768}],['estudiante',{width:820,height:1180}],['estudiante',{width:390,height:844}]]){
  const context=await browser.newContext({viewport}),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(origin);await page.getByRole('button',{name:role==='profesor'?'Probar como profesor':'Probar como estudiante'}).click();
  await page.locator('#chat-input').waitFor();await page.locator('#chat-new').click();await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled);
  check((await page.locator('#chat-provider').innerText()).includes('Demostración sintética'),'Origen real del entorno visible');
  await page.screenshot({path:path.join(target,'workspace-real-'+role+'-'+viewport.width+'.png'),fullPage:true});
  await page.locator('#chat-input').fill(role==='profesor'?'¿Cuáles son mis cursos?':'Muéstrame mis cursos');
  const pending=page.waitForResponse(r=>r.url().endsWith('/api/chatbot/message')&&r.request().method()==='POST');
  await page.locator('#chat-input').press('Enter');const response=await pending;const data=await response.json();
  check(response.status()===200&&data.intent==='COURSES'&&data.demo,'Conversación real autorizada');
  await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled);
  await page.locator('#chat-history').click();await page.locator('#chat-history-list button').first().waitFor();
  check((await page.locator('#chat-history-list').innerText()).includes('mis cursos'),'Historial real recuperado');
  await page.locator('#chat-history').click();
  if(role==='profesor'&&viewport.width===1366){
   await page.locator('#chat-course').selectOption('2');
   await page.locator('#chat-input').fill('Genera el reporte de asistencia de mi curso de octubre');
   const next=page.waitForResponse(r=>r.url().endsWith('/api/chatbot/message')&&r.request().method()==='POST');
   await page.locator('#chat-input').press('Enter');const report=(await(await next).json()).report;
   check(report.synthetic&&report.report_rows===4&&report.metrics.asistencia_pct===100,'Reporte de datos autorizados con cálculo real');
   await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled);
   await page.screenshot({path:path.join(target,'workspace-real-reporte-1366.png'),fullPage:true});
  }
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Sin desbordamientos');
  check(errors.length===0,'Sin errores JS: '+errors.join(';'));await context.close();
 }

 for(const viewport of [{width:1920,height:1080},{width:1366,height:768}]){
  const context=await browser.newContext({viewport}),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(origin);await page.getByRole('button',{name:'Probar como estudiante'}).click();
  await page.locator('#chat-input').waitFor();await page.locator('#chat-new').click();
  await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled);
  await page.locator('#chat-course').selectOption('1');
  for(const question of ['¿Cuál es mi porcentaje de asistencia?']){
   await page.locator('#chat-input').fill(question);
   const response=page.waitForResponse(r=>r.url().endsWith('/api/chatbot/message')&&r.request().method()==='POST');
   await page.locator('#chat-input').press('Enter');const r=await response,data=await r.json();
   check(r.status()===200&&data.demo&&data.intent==='COURSE_STATS','Estadística calculada por el servicio, sin cifras de la referencia');
   await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled);
  }
  check(await page.locator('.message.user').count()===1&&await page.locator('.message.assistant').count()===1,'Intercambio real en pantalla');
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Conversación sin desbordamiento horizontal');
  check(errors.length===0,'Conversación sin errores JS');
  await page.screenshot({path:path.join(target,'workspace-referencia-conversacion-'+viewport.width+'.png'),fullPage:true});
  await context.close();
 }
 console.log('OK: '+checks+' comprobaciones de vista amplia con Chrome, FastAPI, JWT e historial reales; reportes sintéticos calculados, sin MySQL ni audio físico.');
}finally{await browser.close();}
