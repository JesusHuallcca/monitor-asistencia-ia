import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { tool } from './parte7-tools.mjs';
const {chromium}=await tool('playwright');
const origin=process.env.MONITOR_LIVE_DEMO_URL||'http://127.0.0.1:8017';
const url=new URL(origin);
assert(['127.0.0.1','localhost'].includes(url.hostname),'Solo una demo local');
const health=await (await fetch(origin+'/api/health')).json();
assert(health.demo&&health.mysql==='blocked'&&health.storage==='sqlite-memory','No ejecutar contra un backend real');
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1366,height:768}});
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto(origin);
 await page.getByRole('button',{name:'Probar como profesor'}).click();
 await page.waitForURL('**/frontend/profesor/ia.html');
 await page.locator('#chat-panel').waitFor({state:'attached'});if(await page.locator('#chat-panel').isHidden())await page.locator('#chat-launch').click();
 let last;
 for(const [question,intent] of [['Hola','GREETING'],['¿Cuáles son mis cursos?','COURSES'],['¿Y cuál tiene más tardanzas?','LATE_RANKING'],['Muéstrame los registros de octubre','STUDENT_HISTORY']]){
  await page.locator('#chat-input').fill(question);
  const responsePromise=page.waitForResponse(r=>r.url().endsWith('/api/chatbot/message')&&r.request().method()==='POST');
  await page.locator('#chat-input').press('Enter');
  const response=await responsePromise;assert.equal(response.status(),200);
  last=await response.json();assert.equal(last.intent,intent);
  await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled);
 }
 assert.equal(last.demo,true);
 assert.equal(last.context.course_id,2);
 assert.equal(last.data.length,4);
 assert(last.data.every(row=>row.curso==='Programación'&&row.estado==='TARDANZA'));
 assert((await page.locator('#chat-context-summary').innerText()).includes('Programación'));
 await page.locator('.chat-speech summary').click();
 await page.screenshot({path:path.resolve(fileURLToPath(new URL('../../docs/parte7/evidencias/demo-conversacion.png',import.meta.url))),fullPage:true});
 assert.equal(errors.length,0);
 console.log('OK: Chrome + FastAPI + JWT + SQLite reales: saludo → cursos → ranking → registros de octubre. Sin audio ni micrófono físico.');
}finally{await browser.close();}
