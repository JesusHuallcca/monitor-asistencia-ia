import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { tool } from './parte7-tools.mjs';
const {chromium}=await tool('playwright');
const root=path.resolve(fileURLToPath(new URL('..',import.meta.url)));
const evidence=path.resolve(root,'../docs/parte7/evidencias');
await fs.mkdir(evidence,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.png':'image/png','.svg':'image/svg+xml'};
const server=http.createServer(async(req,res)=>{
  const name=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname);
  if(name==='/favicon.ico'){res.writeHead(204);res.end();return;}
  const target=path.resolve(root,'.'+name);
  if(!target.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
  try{const content=await fs.readFile(target);res.writeHead(200,{'Content-Type':types[path.extname(target)]||'application/octet-stream'});res.end(content);}
  catch{res.writeHead(404);res.end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const origin=`http://127.0.0.1:${server.address().port}`;
let browser;
let checks=0;
function check(value,message){assert(value,message);checks++;}
try{
 browser=await chromium.launch({channel:'chrome',headless:true});
 for(const viewport of [{width:1366,height:768},{width:1920,height:1080},{width:390,height:844}]){
  const context=await browser.newContext({viewport});
  await context.addInitScript(()=>{
   sessionStorage.setItem('token','synthetic-test-token');sessionStorage.setItem('rol','profesor');
   window.__audio={spoken:[],starts:0,cancels:0};
   class Utterance{constructor(text){this.text=text;}}
   const synth={speaking:false,voices:[{name:'Español de prueba',lang:'es-PE',voiceURI:'test-es',localService:true}],getVoices(){return this.voices;},addEventListener(){},removeEventListener(){},cancel(){this.speaking=false;this.current=null;window.__audio.cancels++;},speak(item){this.current=item;this.speaking=true;window.__audio.spoken.push({text:item.text,lang:item.lang,voice:item.voice?.voiceURI});}};
   Object.defineProperty(window,'speechSynthesis',{value:synth,configurable:true});Object.defineProperty(window,'SpeechSynthesisUtterance',{value:Utterance,configurable:true});
   class Recognition{constructor(){window.__recognition=this;}start(){window.__audio.starts++;this.onstart?.();}stop(){this.onend?.();}abort(){this.onerror?.({error:'aborted'});this.onend?.();}result(text,final=true){const row=[{transcript:text}];row.isFinal=final;this.onresult({results:[row]});}}
   Object.defineProperty(window,'SpeechRecognition',{value:Recognition,configurable:true});
  });
  const page=await context.newPage();const errors=[];const calls=[];
  page.on('pageerror',error=>errors.push(error.message));
  const longReply='Respuesta sintética completa para comprobar la lectura. '.repeat(12);
  await page.route('**/*',async route=>{
   const request=route.request(),url=new URL(request.url());
   if(url.pathname.startsWith('/api/')){
    if(request.method()==='OPTIONS'){await route.fulfill({status:204,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'Authorization,Content-Type','Access-Control-Allow-Methods':'GET,POST,DELETE,OPTIONS'}});return;}
    let body={};
    if(url.pathname==='/api/users/me')body={id:2,nombres:'Profesor',apellidos:'Sintético',rol:'profesor'};
    else if(url.pathname==='/api/chatbot/context')body={courses:[{id:1,nombre:'Matemática'},{id:2,nombre:'Programación'}],students:[{id:1,nombre:'Perfil sintético 1'}],demo:true};
    else if(url.pathname==='/api/chatbot/history')body=[];
    else if(url.pathname==='/api/chatbot/message'){
     const value=request.postDataJSON();calls.push(value);
     body={reply:longReply,intent:'STUDENT_HISTORY',provider:'local',demo:true,context:{token:'synthetic-context-'+calls.length,course_id:2,student_id:1,period_start:'2026-10-01',period_end:'2026-10-31'}};
    }
    await route.fulfill({status:200,contentType:'application/json',headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*'},body:JSON.stringify(body)});return;
   }
   if(url.origin!==origin){await route.abort();return;}await route.continue();
  });
  await page.goto(origin+'/profesor/ia.html');
  await page.locator('#chat-panel').waitFor({state:'attached'});if(await page.locator('#chat-panel').isHidden())await page.locator('#chat-launch').click();
  await page.locator('#chat-input').fill('Hola');await page.locator('#chat-input').press('Enter');
  await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled&&document.querySelectorAll('.message.assistant').length===1);
  check((await page.evaluate(()=>window.__audio.spoken.length))===0,'Voz apagada por defecto');
  check((await page.locator('#chat-messages').innerText()).includes(longReply.trim()),'Texto completo visible');
  check((await page.locator('#chat-context-summary').innerText()).includes('2026-10-01'),'Período visible');
  await page.locator('.chat-speech summary').click();
  await page.locator('#chat-speech-enabled').check();
  await page.locator('#chat-speech-repeat').click();
  check(await page.locator('#chat-mic').isDisabled(),'Micrófono bloqueado durante lectura');
  check((await page.evaluate(()=>window.__audio.spoken[0].lang))==='es-PE','Lectura en español');
  check((await page.locator('#chat-speech-voice option').count())===1,'Selector de voz');
  await page.evaluate(()=>{for(let i=0;i<30&&speechSynthesis.current;i++){const item=speechSynthesis.current;speechSynthesis.current=null;speechSynthesis.speaking=false;item.onend?.();}});
  check((await page.evaluate(()=>window.__audio.spoken.map(x=>x.text).join('')))===longReply,'Lectura fragmentada sin cortar texto');
  await page.waitForTimeout(300);
  await page.locator('#chat-speech-repeat').click();await page.locator('#chat-speech-stop').click();
  check(await page.locator('#chat-speech-stop').isDisabled(),'Detener descarta cola');
  await page.locator('#chat-speech-repeat').click();await page.locator('#chat-speech-muted').check();
  check(await page.locator('#chat-speech-repeat').isDisabled(),'Silenciar impide repetir');
  await page.locator('#chat-input').fill('¿Y cuál tiene más tardanzas?');await page.locator('#chat-input').press('Enter');
  await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled);
  check(calls[1].context_token==='synthetic-context-1','Seguimiento envía contexto');
  check(!('course_id' in calls[1]),'Contexto recordado sin sobreescribir filtros');
  await page.waitForTimeout(300);
  await page.locator('#chat-mic').click();
  check((await page.evaluate(()=>window.__audio.starts))===0,'No escucha antes del consentimiento');
  await page.locator('#chat-mic-deny').click();
  check((await page.evaluate(()=>window.__audio.starts))===0,'Rechazar conserva texto');
  await page.locator('#chat-mic').click();await page.locator('#chat-mic-allow').click();
  check((await page.evaluate(()=>window.__audio.starts))===1,'Escucha solo tras aceptar');
  await page.evaluate(()=>window.__recognition.result('Muéstrame los registros de octubre',false));
  check((await page.locator('#chat-input').inputValue()).includes('octubre'),'Transcripción parcial visible');
  await page.evaluate(()=>{window.__recognition.result('Muéstrame los registros de octubre');window.__recognition.onend();});
  await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled);
  check(calls[2].source==='voice'&&calls[2].message.includes('octubre'),'Solo transcripción enviada');
  check(!('audio' in calls[2]),'No se envían grabaciones');
  await page.locator('#chat-reset-context').click();
  await page.locator('#chat-input').fill('Mis cursos');await page.locator('#chat-input').press('Enter');
  await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled);
  check(calls[3].context_token===null,'Restablecer elimina contexto temporal');
  await page.locator('#chat-course').selectOption('1');
  await page.locator('#chat-input').fill('Mi historial');await page.locator('#chat-input').press('Enter');
  await page.waitForFunction(()=>!document.querySelector('#chat-input').disabled);
  check(calls[4].course_id===1&&calls[4].student_id===null,'Cambio manual limpia estudiante');
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Sin desbordamiento horizontal: '+await page.evaluate(()=>JSON.stringify({viewport:innerWidth,width:document.documentElement.scrollWidth,overflow:[...document.querySelectorAll('body *')].filter(el=>el.getBoundingClientRect().right>innerWidth+1).slice(0,12).map(el=>({tag:el.tagName,class:el.className,width:el.getBoundingClientRect().width}))})));
  check(await page.locator('#chat-panel').evaluate(el=>{const r=el.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight;}),'Panel dentro de pantalla');
  await page.screenshot({path:path.join(evidence,`chatbot-${viewport.width}.png`),fullPage:true});
  // Recorrido con teclado: Escape cierra y devuelve el foco al lanzador.
  await page.locator('#chat-input').press('Escape');
  check(await page.locator('#chat-panel').isHidden(),'Escape cierra');
  await page.locator('#chat-launch').focus();await page.keyboard.press('Enter');
  check(await page.locator('#chat-panel').isVisible(),'Reabrir con teclado');
  check(errors.length===0,'Sin errores JavaScript: '+errors.join(';'));
  await context.close();
 }
 console.log(`OK: Chrome real, ${checks} comprobaciones en 1366×768, 1920×1080 y 390×844; API y audio simulados, sin micrófono físico.`);
} finally {await browser?.close();await new Promise(resolve=>server.close(resolve));}
