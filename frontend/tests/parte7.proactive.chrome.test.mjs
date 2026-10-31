import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {tool} from './parte7-tools.mjs';
const {chromium}=await tool('playwright');
const origin=process.env.MONITOR_LIVE_DEMO_URL||'http://127.0.0.1:8017';
assert(['127.0.0.1','localhost'].includes(new URL(origin).hostname));
const health=await(await fetch(origin+'/api/health')).json();assert(health.demo&&health.mysql==='blocked'&&health.storage==='sqlite-memory');
let browser=await chromium.launch({channel:'chrome',headless:true}),checks=0;
const evidence=path.resolve(fileURLToPath(new URL('../../docs/parte7/evidencias',import.meta.url)));
function check(value,label){assert(value,label);checks++;}
async function login(viewport,role='profesor'){
 const context=await browser.newContext({viewport});const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(origin);await page.getByRole('button',{name:role==='profesor'?'Probar como profesor':'Probar como estudiante'}).click();
 await page.waitForURL('**/frontend/'+role+'/ia.html');await page.locator('#chat-close').click();await page.locator('#proactive-content').waitFor({state:'visible'});await page.waitForFunction(()=>document.querySelector('#proactive-actions').textContent.length>0);
 return {context,page,errors};
}
async function save(page){
 const pending=page.waitForResponse(r=>r.url().endsWith('/api/chatbot/proactive/actions')&&r.request().method()==='POST');
 await page.locator('#proactive-save').click();const response=await pending;check(response.status()===200,'Borrador creado');const value=await response.json();
 await page.locator('[data-action-id="'+value.id+'"]').waitFor();return value;
}
async function transition(page,action,label,expected){
 const card=page.locator('[data-action-id="'+action.id+'"]');
 const pending=page.waitForResponse(r=>r.url().includes('/actions/'+action.id+'/transition')&&r.request().method()==='POST');
 await card.getByRole('button',{name:label,exact:true}).click();const response=await pending;check(response.status()===200,'Transición autorizada');const value=await response.json();check(value.status===expected,'Estado '+expected);await page.waitForFunction(({id,status})=>document.querySelector('[data-action-id="'+id+'"] .proactive-state')?.textContent===status,{id:action.id,status:({active:'Activa',paused:'Pausada',reviewed:'Borrador aprobado, sin envío'})[expected]});return value;
}
try{
 let {page,context,errors}=await login({width:1366,height:768});
 check(await page.locator('#proactive-title').isVisible(),'Centro en dashboard');
 check(await page.locator('.proactive-suggestion').count()>=2,'Detecta fechas verificadas al abrir el dashboard');
 await page.getByRole('button',{name:'Preparar aviso de clase',exact:true}).first().click();
 // La sugerencia espera la lista autorizada de estudiantes antes de seleccionar la fuente.
 await page.waitForFunction(()=>document.querySelector('#proactive-source').value==='500');
 check(await page.locator('#proactive-source').inputValue()==='500','La sugerencia prepara la fuente sin activar acciones');
 let a=await save(page);check(a.status==='draft'&&a.config.source.type==='sesiones_clase','Fecha de clase verificada; todavía no activa');
 a=await transition(page,a,'Activar recordatorio','active');a=await transition(page,a,'Pausar','paused');a=await transition(page,a,'Activar recordatorio','active');
 const duplicate=await save(page);check(duplicate.id===a.id&&duplicate.status==='active','Repetir configuración no duplica el recordatorio activo');await page.waitForFunction(()=>document.querySelector('#proactive-status').textContent.startsWith('Ya existe'));check(await page.locator('[data-action-id="'+a.id+'"]').count()===1,'Una sola tarjeta para el recordatorio');
 await page.locator('#proactive-kind').selectOption('scheduled_report');await page.locator('#proactive-frequency').selectOption('weekly');
 const weekly=await save(page);check(weekly.status==='draft'&&weekly.frequency==='weekly','Reporte semanal revisable');await transition(page,weekly,'Activar recordatorio','active');
 await page.locator('#proactive-kind').selectOption('communication');
 const draft=await save(page);check(draft.next_run===null&&draft.config.draft_text.includes('no enviado'),'Comunicación no programada para envío');await transition(page,draft,'Aprobar borrador (sin envío)','reviewed');
 await page.locator('#proactive-kind').selectOption('meeting');await page.locator('[name="title"]').fill('Reunión sintética de prueba');await page.locator('[name="event_at"]').fill(new Date(Date.now()+120000).toISOString());
 const meeting=await save(page);check(meeting.config.source.type==='usuario_confirmado','Evento manual declarado por usuario');
 const active=await transition(page,meeting,'Activar recordatorio','active');check(new Date(active.next_run)>new Date(),'Ejecución futura del servidor');
 // Conservar token solo en memoria; jamás se imprime o guarda.
 const token=await page.evaluate(()=>Auth.token());
 check(errors.length===0,'Sin errores JavaScript en edición y activación');
 await browser.close();browser=null;
 await new Promise(resolve=>setTimeout(resolve,4500)); // No hay navegador ni polling JS del dashboard.
 const response=await fetch(origin+'/api/chatbot/proactive/notifications',{headers:{Authorization:'Bearer '+token}});const notes=await response.json();
 const note=notes.find(n=>n.source?.type==='usuario_confirmado'&&n.source.event_at===meeting.config.source.event_at);
 check(!!note,'Recordatorio ejecutado con Chrome cerrado');
 browser=await chromium.launch({channel:'chrome',headless:true});
 for(const viewport of [{width:1366,height:768},{width:1920,height:1080},{width:390,height:844}]){
  const view=await login(viewport);const p=view.page;
  const notification=p.locator('[data-notification-id="'+note.id+'"]');await notification.waitFor();
  check(await notification.isVisible(),'Notificación visible '+viewport.width);
  if(await notification.getByRole('button',{name:'Marcar leída',exact:true}).count())await notification.getByRole('button',{name:'Marcar leída',exact:true}).click();
  await p.locator('#proactive-refresh').click();
  check(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Sin desbordamiento '+viewport.width);
  check(view.errors.length===0,'Sin errores JS '+viewport.width);
  await p.locator('#notificaciones').scrollIntoViewIfNeeded();
  await p.evaluate(()=>window.scrollTo(0,0));
  await p.screenshot({path:path.join(evidence,'proactivo-'+viewport.width+'.png'),fullPage:true});
  await view.context.close();
 }
 const student=await login({width:390,height:844},'estudiante');
 check(await student.page.locator('#proactive-kind option[value="scheduled_report"]').count()===0,'Alumno no programa reportes docentes');
 check(await student.page.locator('#proactive-kind option[value="communication"]').count()===0,'Alumno no prepara comunicaciones docentes');
 const status=await student.page.evaluate(async()=>{const r=await Auth.fetchAutenticado('/api/chatbot/proactive/actions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind:'scheduled_report',course_id:1,frequency:'weekly'})});return r.status;});
 check(status===403,'Backend impide manipular rol desde el navegador');
 check(await student.page.locator('#proactive-inbox').innerText()==='No hay notificaciones disponibles.','No ve notificaciones del profesor');
 await student.context.close();
 console.log('OK: '+checks+' comprobaciones Chrome reales; revisión, activación, pausa, reporte semanal, borrador sin envío, recordatorio con Chrome cerrado, roles y tres resoluciones. Sin notificaciones externas.');
}finally{if(browser)await browser.close();}
