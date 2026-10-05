import { Window } from 'happy-dom';
import fs from 'node:fs';
import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('../components/chatbot.js',import.meta.url),'utf8');
async function setup(supported=true){
 const w=new Window({url:'https://local.test/frontend/estudiante/dashboard.html',settings:{disableCSSFileLoading:true}}); w.document.body.innerHTML='<div class="layout"><button data-open-chat>Chat</button></div>';Object.defineProperty(w,'isSecureContext',{value:true});
 const calls=[];let instance;
 class Speech{constructor(){instance=this;}start(){this.onstart?.();}stop(){this.onend?.();}abort(){this.onerror?.({error:'aborted'});this.onend?.();}result(text,final){const result=[{transcript:text}];result.isFinal=final;this.onresult({results:[result]});}}
 if(supported)w.SpeechRecognition=Speech;else {w.SpeechRecognition=undefined;w.webkitSpeechRecognition=undefined;}
 w.monitorReady=Promise.resolve({user:{nombre:'Ana García',rol:'ESTUDIANTE'},context:{demo:true,courses:[{id:1,nombre:'IA'}],students:[{id:1,nombre:'Ana García'}]},api:async(path,options)=>{if(path.endsWith('/history'))return [];calls.push(JSON.parse(options.body));return {reply:'Respuesta segura',provider:'local',demo:true};}});
 w.eval(source);await new Promise(r=>setTimeout(r,20));const $=id=>w.document.getElementById(id);
 $('chat-launch').click();await new Promise(r=>setTimeout(r,10));return {w,$,calls,get speech(){return instance;}};
}
const wait=()=>new Promise(r=>setTimeout(r,10));
let t=await setup();assert.equal(t.$('chat-panel').hidden,false);assert.equal(t.w.document.querySelector('.layout').inert,true);t.$('chat-expand').click();assert(t.$('chat-panel').classList.contains('expanded'));
t.$('chat-mic').click();assert.equal(t.speech.lang,'es-PE');t.speech.result('Cuántos faltaron',false);assert.equal(t.$('chat-input').value,'Cuántos faltaron');assert.equal(t.calls.length,0);t.speech.result('Cuántos faltaron hoy',true);t.speech.onend();await wait();assert.equal(t.calls.length,1);assert.equal(t.calls[0].source,'voice');assert.equal(t.calls[0].message,'Cuántos faltaron hoy');assert.match(t.$('chat-messages').textContent,/Transcrito desde tu voz/);assert.equal(t.$('chat-input').disabled,false);
t.$('chat-input').value='Borrador previo';t.$('chat-mic').click();t.speech.result('No enviar',true);t.$('voice-cancel').click();await wait();assert.equal(t.calls.length,1);assert.equal(t.$('chat-input').value,'Borrador previo');
t.$('chat-mic').click();t.speech.onerror({error:'not-allowed'});t.speech.onend();await wait();assert.equal(t.calls.length,1);assert.match(t.$('chat-status').textContent,/Permite el micrófono/);assert.equal(t.$('chat-input').disabled,false);
t.$('chat-mic').click();t.speech.result('No enviar al cerrar',true);t.$('chat-close').click();await wait();assert.equal(t.calls.length,1);assert.equal(t.$('chat-panel').hidden,true);assert.equal(t.w.document.querySelector('.layout').inert,false);
await t.w.happyDOM.close();
t=await setup(false);assert.equal(t.$('chat-mic').disabled,true);t.$('chat-input').value='Mis cursos';t.$('chat-form').dispatchEvent(new t.w.Event('submit',{bubbles:true,cancelable:true}));await wait();assert.equal(t.calls[0].source,'text');assert.equal(t.$('chat-mic').disabled,true);await t.w.happyDOM.close();
console.log('OK: panel, expandir, transcripción parcial/final, envío por voz, cancelación, permiso denegado, cierre durante audio y alternativa de texto.');
