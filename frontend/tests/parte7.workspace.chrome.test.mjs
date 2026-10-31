/* Pruebas de presentación con fixtures explícitas. Sin MySQL, cámara ni datos reales. */
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {tool} from './parte7-tools.mjs';
const {chromium}=await tool('playwright');
const root=path.resolve(fileURLToPath(new URL('..',import.meta.url)));
const evidence=path.resolve(root,'../docs/parte7/evidencias');
const server=http.createServer(async(req,res)=>{
 const name=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname);
 const target=path.resolve(root,'.'+name);
 if(!target.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
 try{const content=await fs.readFile(target);const type={'.html':'text/html','.js':'text/javascript','.css':'text/css','.png':'image/png','.svg':'image/svg+xml'}[path.extname(target)]||'application/octet-stream';res.writeHead(200,{'Content-Type':type});res.end(content);}
 catch{res.writeHead(404);res.end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const origin='http://127.0.0.1:'+server.address().port;
const browser=await chromium.launch({channel:'chrome',headless:true});
let checks=0;const pagesChecked=[],emptyPages=[];
function check(value,label){assert(value,label);checks++;}
async function setup(role,viewport){
 const context=await browser.newContext({viewport});
 await context.addInitScript(role=>{sessionStorage.setItem('token','synthetic-ui-fixture');sessionStorage.setItem('rol',role);},role);
 const page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 let history=[],deleted=0,unread=0;
 await page.route('**/*',async route=>{
  const req=route.request(),url=new URL(req.url());
  if(url.pathname.startsWith('/api/')){
   if(req.method()==='OPTIONS'){await route.fulfill({status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'Authorization,Content-Type','Access-Control-Allow-Methods':'GET,POST,DELETE,PUT,OPTIONS'}});return;}
   let body={},status=200;
   const who={id:role==='profesor'?1:2,nombres:role==='profesor'?'Docente':'Ana',apellidos:'Sintética',rol:role,username:'fixture',email:'fixture@example.test',creado_en:'2026-01-01T00:00:00'};
   const course={id:1,codigo:'TEST-1',nombre:'Curso sintético para prueba de interfaz',periodo:'2026',activo:true};
   if(url.pathname==='/api/users/me'||url.pathname==='/api/users/me/profile'||url.pathname==='/api/users/perfil')body=who;
   else if(url.pathname==='/api/chatbot/context')body={demo:true,courses:[course],students:[{id:1,nombre:'Perfil sintético autorizado'}]};
   else if(url.pathname==='/api/chatbot/history'){if(req.method()==='DELETE'){deleted++;history=[];}body=history;}
   else if(url.pathname==='/api/chatbot/message'){const value=req.postDataJSON();const reply='Respuesta sintética de prueba de legibilidad. No representa datos académicos reales.\n'.repeat(28);history.push({question:value.message,reply});body={reply,intent:'HELP',provider:'local',demo:true};}
   else if(url.pathname==='/api/chatbot/proactive/notifications')body=Array.from({length:unread},(_,i)=>({id:String(i),state:'unread'}));
   else if(url.pathname==='/api/chatbot/proactive/status')body={available:false,message:'Almacenamiento no habilitado en la prueba de interfaz.'};
   else if(url.pathname==='/api/cursos'||url.pathname.startsWith('/api/admin/usuarios'))body=[];
   else if(url.pathname==='/api/cursos/1')body=course;
   else if(url.pathname.endsWith('/mis-notas'))body={filas:[],promedio_actual:null};
   else if(url.pathname.endsWith('/libro'))body={evaluaciones:[],alumnos:[]};
   else if(url.pathname.endsWith('/profesores')||url.pathname.endsWith('/estudiantes'))body=[];
   else if(url.pathname.startsWith('/api/attendance/my-course'))body={registros:[],promedio:null,presentes:0};
   else if(url.pathname==='/api/attendance/current-session-status')body={sesion_activa:false,ya_registrada:false};
   else{status=503;body={detail:'Servicio fuera del alcance de esta prueba de interfaz.'};}
   await route.fulfill({status,contentType:'application/json',headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},body:JSON.stringify(body)});return;
  }
  if(url.origin!==origin){await route.abort();return;}await route.continue();
 });
 return {context,page,errors,get deleted(){return deleted;},setUnread(value){unread=value;}};
}
async function open(page){await page.locator('#chat-launch').waitFor({state:'attached'});await page.locator('#chat-panel').waitFor({state:'attached'});if(await page.locator('#chat-panel').isHidden())await page.locator('#chat-launch').click();await page.locator('#chat-input').waitFor();}
try{
 for(const role of ['estudiante','profesor']){
  const h=await setup(role,{width:1366,height:768});
  for(const file of (await fs.readdir(path.join(root,role))).filter(f=>f.endsWith('.html'))){
   if((await fs.stat(path.join(root,role,file))).size===0){emptyPages.push(role+'/'+file);continue;}
   await h.page.goto(origin+'/'+role+'/'+file+(file==='curso.html'?'?id=1':''));
   await h.page.locator('#chat-launch').waitFor({state:'attached'});
   check(await h.page.locator('#monitor-chat-root').count()===1,'Un componente: '+role+'/'+file);
   check((await h.page.locator('.admin-menu').innerText()).includes('Cerrar sesión'),'Menú montado: '+file);
   check(!(await h.page.locator('.admin-menu').innerText()).includes('Asistente IA'),'Sin entrada redundante: '+role+'/'+file);
   await open(h.page);
   const geometry=await h.page.evaluate(()=>{const a=document.querySelector('.admin-menu').getBoundingClientRect(),c=document.querySelector('#chat-panel').getBoundingClientRect();return {a:{left:a.left,right:a.right},c:{left:c.left,right:c.right,top:c.top,bottom:c.bottom},width:innerWidth,height:innerHeight};});
   check(Math.abs(geometry.c.left-geometry.a.right)<2&&Math.abs(geometry.c.right-geometry.width)<2,'Ocupa área derecha: '+file);
   check(await h.page.locator('.admin-menu').evaluate(el=>!el.inert&&!el.closest('[inert]')),'Sidebar accesible: '+file);
   const url=h.page.url();await h.page.locator('#chat-input').fill('Borrador conservado');
   await h.page.locator('#chat-close').click();
   check(h.page.url()===url&&await h.page.locator('#chat-panel').isHidden(),'Retorno sin navegar: '+file);
   check(await h.page.locator('#chat-launch').isVisible()&&await h.page.locator('#chat-launch').evaluate(el=>{const r=el.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight;}),'Robot flotante visible y dentro de pantalla: '+role+'/'+file);

   await open(h.page);check(await h.page.locator('#chat-input').inputValue()==='Borrador conservado','Conserva estado: '+file);
   check(h.errors.length===0,'Sin errores JavaScript en '+file+': '+h.errors.join(';'));
   pagesChecked.push(role+'/'+file);
  }
  await h.context.close();
 }
 for(const role of ['estudiante','profesor']){
  for(const viewport of [{width:1920,height:1080},{width:1366,height:768},{width:820,height:1180},{width:390,height:844}]){
   const h=await setup(role,viewport),page=h.page;
   await page.goto(origin+'/'+role+'/ia.html');await page.locator('#chat-input').waitFor();
   check(await page.locator('#chat-panel').isVisible(),'Ruta directa abre vista amplia');
   check(await page.locator('#chat-name').innerText()==='Asistente Virtual IA','Título compartido');
   check((await page.locator('#chat-greeting').innerText()).includes(role==='profesor'?'Docente':'Ana'),'Saludo autenticado');
   check(await page.locator('#chat-launch-count').isHidden(),'Sin notificaciones inventadas');
   check(await page.locator('.suggestions > .suggestion').count()===5,'Cinco preguntas principales según el rol');
   check(await page.locator('.chat-hero').evaluate(el=>{const [robot,copy]=el.children;return robot.getBoundingClientRect().right<=copy.getBoundingClientRect().left;}),'Saludo junto al robot');
   if(viewport.width>=1366)check(await page.locator('.suggestions').evaluate(el=>new Set([...el.children].map(c=>Math.round(c.getBoundingClientRect().top))).size===1),'Cinco preguntas en una fila de escritorio');
   await page.locator('#chat-tools-toggle').click();await page.waitForFunction(()=>document.querySelector('#chat-tools-toggle').getAttribute('aria-expanded')==='true');
   check(await page.locator('#chat-speech-tools').evaluate(el=>el.open),'Acceso a herramientas de voz desde el compositor');
   await page.locator('#chat-tools-toggle').click();

   check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Sin overflow '+role+' '+viewport.width);
   check(await page.locator('#chat-input').evaluate(el=>{const r=el.getBoundingClientRect();return r.bottom<=innerHeight&&r.top>=0;}),'Entrada visible');
   if(viewport.width<=820){
    await page.locator('#chat-menu').click();await page.waitForFunction(()=>document.querySelector('.admin-menu').getBoundingClientRect().left>=-1);
    check(await page.locator('.admin-menu').evaluate(el=>el.getBoundingClientRect().left>=-1),'Drawer accesible');
    await page.locator('.panel-nav-close').click();await page.waitForFunction(()=>document.querySelector('.admin-menu').getBoundingClientRect().right<=0);
   }else check(await page.locator('.admin-menu').isVisible(),'Sidebar visible');
   if(role==='profesor')check(await page.locator('.admin-menu .pronto').count()===5,'Módulos faltantes indicados como pendientes');
   else check((await page.locator('.admin-menu nav').innerText()).includes('Mi asistencia'),'Menú estudiantil conserva asistencia');
   await fs.mkdir(evidence,{recursive:true});
   await page.screenshot({path:path.join(evidence,'workspace-'+role+'-'+viewport.width+'.png'),fullPage:true});
   await page.locator('#chat-input').fill('Consulta sintética para verificar una respuesta extensa');
   await page.locator('#chat-input').press('Enter');
   await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled&&document.querySelectorAll('.message.assistant').length===1);
   check((await page.locator('.message.assistant').innerText()).includes('No representa datos académicos reales'),'Texto íntegro sin datos ficticios presentados como reales');
   check(await page.locator('.chat-user-avatar').innerText()===(role==='profesor'?'D':'A'),'Inicial del usuario autenticado');
   check(await page.locator('#chat-welcome').evaluate(el=>!el.hidden),'Saludo conservado al conversar; se desplaza con el contenido');

   await page.locator('#chat-new').click();
   await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled);
   check(h.deleted===0,'Nueva conversación no borra historial');
   await page.locator('#chat-history').click();await page.locator('#chat-history-list button').waitFor();
   check((await page.locator('#chat-history-list').innerText()).includes('Consulta sintética'),'Historial conservado');
   h.setUnread(2);await page.locator('#chat-close').click();await open(page);
   await page.waitForFunction(()=>document.querySelector('#chat-notification-count').textContent==='2');
   check(await page.locator('#chat-notification-count').innerText()==='2','Contador procede del servicio');
   check(h.errors.length===0,'Sin errores JS responsive: '+h.errors.join(';'));
   await h.context.close();
  }
 }
 for(const role of ['admin','superadmin']){
  const h=await setup(role,{width:1366,height:768});await h.page.goto(origin+'/admin/usuarios.html');
  await h.page.locator('.admin-menu nav a').first().waitFor();
  check(await h.page.locator('#monitor-chat-root').count()===0,'No inyecta componente en panel '+role);
  check(!(await h.page.locator('body').getAttribute('class')).includes('monitor-chat-active'),'No altera superficie '+role);
  check(h.errors.length===0,'Panel '+role+' sin errores: '+h.errors.join(';'));await h.context.close();
 }
 const summary={checks,pagesChecked,emptyLegacyPlaceholders:emptyPages,viewports:['1920x1080','1366x768','820x1180','390x844'],api:'synthetic_ui_fixtures',physical_microphone_tested:false};
 await fs.writeFile(path.join(evidence,'workspace-verificacion.json'),JSON.stringify(summary,null,2)+'\n');
 console.log('OK: '+checks+' comprobaciones de interfaz; '+pagesChecked.length+' páginas funcionales, ambos roles académicos y administración sin cambios. Fixtures explícitas; sin MySQL ni cámara.');
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
