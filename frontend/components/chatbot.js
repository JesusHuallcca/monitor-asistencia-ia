/* Integración reutilizable: cargar dashboard.js (monitorReady) antes de este script. */
'use strict';
(async()=>{
 if(window.__monitorChatMounting||document.getElementById('monitor-chat-root'))return;
 window.__monitorChatMounting=true;
 const scriptUrl=new URL(document.currentScript?.src || '/frontend/components/chatbot.js',location.href);
 const ready=await window.monitorReady; if(!ready){window.__monitorChatMounting=false;return;}
 const {user,context,api}=ready;
 if(['ESTUDIANTE','PROFESOR'].includes(user.rol)){
  document.body.dataset.rol=user.rol.toLowerCase();
  const aside=document.querySelector('.admin-menu,.dashboard-sidebar');
  aside?.classList.add('admin-menu');
  if(user.rol==='ESTUDIANTE')aside?.querySelectorAll('a[href="ia.html"]').forEach(link=>link.remove());
  if(!window.PanelNavigation)await new Promise(resolve=>{const script=document.createElement('script');script.src=new URL('../js/panel-navigation.js',scriptUrl).href;script.onload=resolve;script.onerror=resolve;document.body.append(script);});
  window.PanelNavigation?.mount();
 }
 const link=document.createElement('link');link.rel='stylesheet';link.href=new URL('../css/chatbot.css',scriptUrl).href;document.head.append(link);
 const avatarUrl=new URL('../assets/img/chatbot-monitor.png',scriptUrl).href;
 const host=document.createElement('div');host.id='monitor-chat-root';host.innerHTML=`
 <button class="chat-launch" id="chat-launch" aria-label="Abrir asistente Monitor IA" aria-controls="chat-panel" aria-expanded="false"><img class="chat-avatar" src="${avatarUrl}" alt="" /><span id="chat-launch-count" class="chat-notification-count" hidden></span></button>

 <section class="chat-panel" id="chat-panel" role="region" aria-labelledby="chat-name" hidden>
 <header class="chat-header"><div class="chat-title"><button type="button" class="icon-btn chat-mobile-menu" id="chat-menu" aria-controls="panel-navigation" aria-expanded="false" aria-label="Abrir menú de navegación">☰</button><img class="chat-avatar chat-header-avatar" src="${avatarUrl}" alt="" /><div><strong id="chat-name">Asistente Virtual IA</strong><small class="chat-subtitle">Tu asistente académico en lenguaje natural</small></div></div><div class="chat-account"><span id="chat-provider"></span></div><div class="chat-actions"><button type="button" class="chat-header-action" id="chat-new" aria-label="Nueva conversación" title="Nueva conversación"><span aria-hidden="true">＋</span><span class="chat-action-label">Nueva conversación</span></button><button type="button" class="chat-header-action" id="chat-history" aria-label="Consultar historial" aria-expanded="false" aria-controls="chat-history-panel" title="Consultar historial"><span aria-hidden="true">◷</span><span class="chat-action-label">Historial</span></button><button type="button" class="icon-btn" id="chat-notifications" aria-label="Recordatorios y notificaciones" title="Recordatorios y notificaciones"><svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></svg><span id="chat-notification-count" class="chat-notification-count" hidden></span></button><button type="button" class="icon-btn" id="chat-close" aria-label="Cerrar asistente" title="Volver a la página">×</button></div></header>
 <div class="chat-filters"><select id="chat-course" aria-label="Filtrar curso"><option value="">Todos mis cursos</option></select><select id="chat-student" aria-label="Filtrar estudiante"><option value="">Mi ámbito completo</option></select></div>
 <div class="chat-context"><span id="chat-context-summary" role="status">Contexto temporal · 20 minutos</span><button type="button" id="chat-reset-context">Restablecer contexto</button></div>
 <div class="chat-feed" id="chat-feed"><div class="chat-content"><div class="chat-welcome" id="chat-welcome"><div class="chat-hero"><img class="chat-welcome-avatar" src="${avatarUrl}" alt="Robot Monitor IA" /><div class="chat-hero-copy"><h2 id="chat-greeting"></h2><p class="chat-question">¿En qué puedo ayudarte hoy?</p><p class="chat-intro">Tu información académica, en una conversación.</p></div></div><div class="suggestions" aria-label="Preguntas rápidas"></div><div class="chat-more-prompts" aria-label="Más consultas"></div></div><section id="chat-history-panel" class="chat-history-panel" aria-label="Historial de conversaciones" hidden><div class="chat-history-heading"><strong>Tu historial</strong><button type="button" id="chat-history-clear">Eliminar mi historial</button></div><p>Solo consultas accesibles con tus permisos actuales. Selecciona una para volver a preguntarla.</p><ul id="chat-history-list"></ul><div id="chat-history-confirm" hidden><p>¿Eliminar tu historial guardado? Esta acción no se puede deshacer.</p><button type="button" id="chat-history-delete">Confirmar eliminación</button><button type="button" id="chat-history-cancel">Conservar historial</button></div></section><div id="chat-messages" role="log" aria-live="polite" aria-relevant="additions"></div></div></div>
 <footer class="chat-footer">
 <details class="chat-speech" id="chat-speech-tools"><summary>Voz del asistente</summary><div class="chat-speech-controls">
 <label><input type="checkbox" id="chat-speech-enabled"> Leer respuestas</label>
 <label><input type="checkbox" id="chat-speech-muted"> Silenciar</label>
 <label class="chat-voice-label">Voz en español <select id="chat-speech-voice" aria-label="Voz en español"></select></label>
 <button type="button" id="chat-speech-stop" disabled>Detener reproducción</button>
 <button type="button" id="chat-speech-repeat" disabled>Repetir respuesta</button>
 <span id="chat-audio-status" role="status" aria-live="polite">Lectura desactivada. Puedes usar solo texto.</span></div></details>
 <div id="chat-mic-consent" class="chat-mic-consent" role="group" aria-label="Permiso de micrófono" hidden>
 <p>¿Permites usar el micrófono para esta página? El navegador pedirá permiso. La transcripción puede usar su servicio de voz externo. Se enviará solo el texto; esta aplicación no guarda grabaciones.</p>
 <button type="button" id="chat-mic-allow">Permitir micrófono</button><button type="button" id="chat-mic-deny">Seguir con texto</button></div>
 <form id="chat-form"><div class="composer"><button type="button" class="icon-btn chat-tools-toggle" id="chat-tools-toggle" aria-label="Configurar herramientas de voz" aria-controls="chat-speech-tools" aria-expanded="false" title="Herramientas de voz">+</button><textarea id="chat-input" aria-label="Pregunta al asistente" placeholder="Pregunta sobre tus cursos, asistencia o actividades…" rows="1" maxlength="2000"></textarea><div class="composer-tools"><small id="voice-hint">Escribe o pregunta con tu voz</small><div class="composer-buttons"><button type="button" class="chat-cancel" id="voice-cancel" hidden>Cancelar audio</button><button type="button" class="icon-btn" id="chat-mic" aria-label="Preguntar por voz" aria-pressed="false" title="Hablar y consultar al terminar"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8"/></svg></button><button type="submit" class="send-btn" id="chat-send" aria-label="Enviar pregunta"><svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="m21 3-7 18-4-7-7-4L21 3Z"/><path d="m10 14 7-7"/></svg></button></div></div></div><div id="chat-status" class="chat-status" role="status" aria-live="polite"></div><p class="chat-hint">Solo puedes consultar información asociada a tu cuenta.</p></form></footer></section>`;
 const surface=document.querySelector('.admin-principal,.dashboard-main')||document.querySelector('main.main')||document.body;
 surface.append(host);
 const $=id=>host.querySelector('#'+id);const panel=$('chat-panel'),input=$('chat-input'),status=$('chat-status'),feed=$('chat-feed'),messages=$('chat-messages'),mic=$('chat-mic');
 $('chat-menu').setAttribute('aria-controls',document.querySelector('.admin-menu,.dashboard-sidebar')?.id||'panel-navigation');
 $('chat-provider').textContent=({ADMIN:'Administrador',PROFESOR:'Profesor',ESTUDIANTE:'Estudiante'})[user.rol]||'Mi cuenta';$('chat-provider').textContent+=context.demo?' · Demostración sintética':' · Ámbito autorizado';const firstName=user.nombre.trim().split(/\s+/)[0]||'de nuevo';
 $('chat-greeting').append(document.createTextNode('Hola, '));const greetingName=document.createElement('span');greetingName.textContent=firstName;$('chat-greeting').append(greetingName);
 $('chat-tools-toggle').onclick=()=>{$('chat-speech-tools').open=!$('chat-speech-tools').open;};
 $('chat-speech-tools').addEventListener('toggle',()=>{$('chat-tools-toggle').setAttribute('aria-expanded',String($('chat-speech-tools').open));});
 input.addEventListener('input',()=>{input.style.height='auto';input.style.height=Math.min(input.scrollHeight,110)+'px';});
 const promptIcons={
  attendance:'<circle cx="12" cy="12" r="9"/><path d="M12 3v9h9"/>',
  absent:'<circle cx="12" cy="8" r="4"/><path d="M5 21v-2a7 7 0 0 1 14 0v2H5Z"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 6v6h5"/>',
  courses:'<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>',
  calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 2v6M17 2v6M3 11h18"/>',
  report:'<path d="M6 3h9l4 4v14H6V3Z M14 3v5h5M9 12h7M9 16h7"/>'
 };
 const prompts=user.rol==='ESTUDIANTE'?[
  ['attendance','¿Cuál es mi porcentaje de asistencia?','¿Cuál es mi porcentaje de asistencia?'],
  ['absent','¿Cuántas faltas tengo?','¿Cuántas faltas tengo?'],
  ['clock','¿Cuántas tardanzas tengo?','¿Cuántas tardanzas tengo?'],
  ['courses','Muéstrame mis cursos','Muéstrame mis cursos'],
  ['calendar','¿Cuál es mi próxima clase?','¿Cuál es mi próxima clase?'],
  ['Mis reportes','Descarga mi historial de asistencia'],
  ['Mis calificaciones','Genera mi resumen académico'],
  ['Mis recordatorios','Recuérdame mi próxima clase']
 ]:[
  ['attendance','Resumen de asistencia','Dame un resumen de asistencia'],
  ['clock','Tardanzas de esta semana','Muéstrame las tardanzas de esta semana'],
  ['courses','Muéstrame mis cursos','Muéstrame mis cursos'],
  ['report','Preparar un reporte','Genera un reporte de asistencia'],
  ['calendar','¿Cuál es mi próxima clase?','¿Cuál es mi próxima clase?'],
  ['Comprender K-Means','Explícame qué es K-Means'],
  ['Evaluación de modelos','Genera un reporte de evaluación de modelos'],
  ['Programar reporte semanal','Programa un reporte semanal']
 ];
 for(const [i,item] of prompts.entries()){
  const button=document.createElement('button');button.type='button';button.className='suggestion';button.dataset.question=item.at(-1);
  if(i<5){const icon=document.createElement('span');icon.className='suggestion-icon';icon.setAttribute('aria-hidden','true');icon.innerHTML='<svg width="23" height="23" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'+promptIcons[item[0]]+'</svg>';const title=document.createElement('span');title.textContent=item[1];button.append(icon,title);host.querySelector('.suggestions').append(button);}
  else {button.textContent=item[0];host.querySelector('.chat-more-prompts').append(button);}
 }
 for(const [select,items] of [[$('chat-course'),context.courses],[$('chat-student'),context.students]])for(const item of items){const o=document.createElement('option');o.value=item.id;o.textContent=item.nombre;select.append(o);}
 if(user.rol==='ESTUDIANTE'){$('chat-student').hidden=true;$('chat-course').style.width='100%';}
 let backgroundStates=[],pageScroll=0,historyEntries=[];
 const viewport=()=>{const height=(window.visualViewport?.height||window.innerHeight)+'px';host.style.setProperty('--chat-viewport',height);surface.style.setProperty('--chat-viewport',height);};
 viewport();window.visualViewport?.addEventListener('resize',viewport);window.addEventListener('resize',viewport);
 let conversationToken=null,selectionChanges={},lastReply='',ttsActive=false,speechGeneration=0,micConsent=false,micBlockedUntil=0;
 const synthesis=window.speechSynthesis,Utterance=window.SpeechSynthesisUtterance;
 const ttsSupported=!!(synthesis&&Utterance);
 const speechEnabled=$('chat-speech-enabled'),speechMuted=$('chat-speech-muted'),voiceSelect=$('chat-speech-voice'),audioStatus=$('chat-audio-status');
 let busy=false,listening=false,recognition=null,lastFocus=null,cancelled=false,failed=false,finalTranscript='',originalDraft='',historyPromise=null;
 function updateSpeechControls(){
   $('chat-speech-stop').disabled=!ttsActive;
   $('chat-speech-repeat').disabled=!ttsSupported||!speechEnabled.checked||speechMuted.checked||!lastReply||listening||busy;
   voiceSelect.disabled=!ttsSupported||listening;
 }
 function stopSpeaking(){const wasSpeaking=ttsActive||synthesis?.speaking;speechGeneration++;if(ttsSupported)synthesis.cancel();ttsActive=false;if(wasSpeaking)micBlockedUntil=Date.now()+250;audioStatus.textContent='Reproducción detenida.';updateSpeechControls();}
 function populateVoices(){
   if(!ttsSupported)return;
   const selected=voiceSelect.value;voiceSelect.replaceChildren();
   const voices=synthesis.getVoices().filter(v=>/^es(?:-|$)/i.test(v.lang));
   for(const voice of voices){const option=document.createElement('option');option.value=voice.voiceURI;option.textContent=voice.name+' · '+voice.lang+(voice.localService?' · local':'');voiceSelect.append(option);}
   if(voices.some(v=>v.voiceURI===selected))voiceSelect.value=selected;
   else if(voices.length)voiceSelect.value=(voices.find(v=>v.lang.toLowerCase()==='es-pe')||voices[0]).voiceURI;
   else {const option=document.createElement('option');option.value='';option.textContent='Español del navegador';voiceSelect.append(option);}
 }
 function readReply(text){
   if(!ttsSupported||!speechEnabled.checked||speechMuted.checked||listening||panel.hidden||!text)return;
   stopSpeaking();const generation=speechGeneration;
   // Fragmentos cortos para evitar cortes del motor; el texto completo queda visible.
   const chunks=text.match(/[\s\S]{1,220}(?:\s|$)|[\s\S]{1,220}/g)||[text];let index=0;
   ttsActive=true;controls();audioStatus.textContent='Leyendo respuesta. El micrófono está bloqueado.';
   const next=()=>{
     if(generation!==speechGeneration||panel.hidden||speechMuted.checked||!speechEnabled.checked)return;
     if(index===chunks.length){ttsActive=false;micBlockedUntil=Date.now()+250;audioStatus.textContent='Lectura finalizada.';controls();return;}
     const utterance=new Utterance(chunks[index++]);utterance.lang='es-PE';utterance.rate=1;utterance.volume=1;
     utterance.voice=synthesis.getVoices().find(v=>v.voiceURI===voiceSelect.value)||null;
     utterance.onend=next;
     utterance.onerror=()=>{if(generation!==speechGeneration)return;ttsActive=false;audioStatus.textContent='No se pudo leer la respuesta. Puedes leer el texto o pulsar Repetir.';controls();};
     try{synthesis.speak(utterance);}catch{utterance.onerror();}
   };next();
 }
 function resetContext(){conversationToken=null;selectionChanges={};$('chat-course').value='';$('chat-student').value='';$('chat-context-summary').textContent='Contexto restablecido · sin período seleccionado';}
 function applyContext(value){
   if(!value)return;conversationToken=value.token;
   $('chat-course').value=value.course_id?String(value.course_id):'';
   if(user.rol!=='ESTUDIANTE')$('chat-student').value=value.student_id?String(value.student_id):'';
   const course=context.courses.find(c=>c.id===value.course_id)?.nombre||'Todos mis cursos';
   const student=context.students.find(c=>c.id===value.student_id)?.nombre;
   $('chat-context-summary').textContent=[course,student,value.period_start?value.period_start+' a '+value.period_end:'Sin filtro de fecha','20 min'].filter(Boolean).join(' · ');
 }
 $('chat-reset-context').onclick=()=>{resetContext();status.textContent='La siguiente consulta comenzará sin selecciones previas.';};
 for(const [id,field] of [['chat-course','course_id'],['chat-student','student_id']])$(id).addEventListener('change',()=>{selectionChanges[field]=$(id).value?Number($(id).value):null;if(field==='course_id'){$('chat-student').value='';selectionChanges.student_id=null;}});
 speechEnabled.disabled=!ttsSupported;speechMuted.disabled=!ttsSupported;
 speechEnabled.onchange=()=>{if(!speechEnabled.checked)stopSpeaking();audioStatus.textContent=speechEnabled.checked?'Se leerán las próximas respuestas.':'Lectura desactivada.';controls();};
 speechMuted.onchange=()=>{if(speechMuted.checked)stopSpeaking();audioStatus.textContent=speechMuted.checked?'Voz silenciada.':'Voz disponible para la próxima respuesta.';controls();};
 $('chat-speech-stop').onclick=()=>{stopSpeaking();controls();};$('chat-speech-repeat').onclick=()=>readReply(lastReply);
 if(ttsSupported){populateVoices();synthesis.addEventListener?.('voiceschanged',populateVoices);}else audioStatus.textContent='Síntesis de voz no disponible. Puedes usar todo el asistente con texto.';
 function scroll(){feed.scrollTop=feed.scrollHeight;}
 function add(role,text,meta=''){
  const row=document.createElement('div');row.className='message '+role;
  if(role==='assistant'){const avatar=document.createElement('img');avatar.className='chat-avatar chat-message-avatar';avatar.src=avatarUrl;avatar.alt='';row.append(avatar);}
  const bubble=document.createElement('div');bubble.className='bubble';bubble.textContent=text;
  if(meta){const small=document.createElement('div');small.className='meta';small.textContent=meta;bubble.append(small);}
  row.append(bubble);
  if(role==='user'){const avatar=document.createElement('span');avatar.className='chat-user-avatar';avatar.textContent=Array.from(firstName)[0].toLocaleUpperCase('es');avatar.setAttribute('aria-hidden','true');row.append(avatar);}
  messages.append(row);scroll();return row;
 }
 function controls(){input.disabled=busy||listening;$('chat-send').disabled=busy||listening;$('chat-new').disabled=busy||listening;$('chat-history').disabled=busy||listening;$('chat-history-delete').disabled=busy||listening;mic.disabled=busy||ttsActive;mic.classList.toggle('listening',listening);mic.setAttribute('aria-pressed',String(listening));mic.setAttribute('aria-label',listening?'Terminar audio y consultar':'Preguntar por voz');$('voice-cancel').hidden=!listening;$('chat-reset-context').disabled=busy||listening;host.querySelectorAll('.suggestion,select').forEach(e=>e.disabled=busy||listening);updateSpeechControls();}
 function reportElement(tag,text,className=''){const element=document.createElement(tag);if(text!==undefined)element.textContent=text;if(className)element.className=className;return element;}
 function showML(row,ml){
   if(!ml||ml.status==='educational')return;
   const panel=reportElement('section',undefined,'chat-ml');panel.setAttribute('aria-label','Resultado de consulta ML');
   const labels={available:'Disponible',pending:'Pendiente',unavailable:'No disponible'};
   panel.append(reportElement('h3','Consulta de modelo'),reportElement('strong',labels[ml.status]||ml.status,'chat-ml-state'));
   const origins={sintetico:'Datos sintéticos',sistema:'Datos del sistema autorizados',no_verificado:'Origen no verificado',no_disponible:'Sin resultado disponible'};
   panel.append(reportElement('p',origins[ml.origin]||'Consulta educativa'));
   panel.append(reportElement('p','Versión: '+(ml.model_version||'No disponible; no se atribuye una versión de modelo')));
   if(ml.training_origin)panel.append(reportElement('p','Entrenamiento: '+(origins[ml.training_origin]||ml.training_origin)));
   if(ml.variables?.length){const details=reportElement('details');details.append(reportElement('summary','Variables utilizadas ('+ml.variables.length+')'),reportElement('p',ml.variables.join(' · ')));panel.append(details);}
   if(ml.dependencies?.length)panel.append(reportElement('p','Pendiente: '+ml.dependencies.join('; ')));
   panel.append(reportElement('small','Sin reentrenamiento. Asistir incluye llegar tarde; no equivale a puntualidad. No se utilizan datos faciales de EmoScan.'));
   row.querySelector('.bubble').append(panel);
 }
 function showReport(row,report){
   const container=reportElement('section',undefined,'chat-report');container.setAttribute('aria-label','Vista previa del reporte académico');
   container.append(reportElement('h3',report.title),reportElement('p',report.message,'chat-report-note'));
   container.append(reportElement('p',[report.mode_label||(report.synthetic?'Datos sintéticos':'Datos académicos autorizados'),report.source,(report.courses||[]).map(c=>c.nombre).join(', '),(report.periods||[]).join(' / '),'Generado: '+report.generated_at].join(' · '),'chat-report-meta'));
   const metrics=report.metrics||{},cards=reportElement('div',undefined,'chat-report-metrics');
   for(const [label,value] of (report.kind==='ml_evaluation'?[['Modelos documentados',report.models.length],['Comparación equivalente','No'],['Ganador','No aplica']]:[['Registros base',metrics.registros],['Filas del reporte',report.report_rows],['Asistencia',metrics.asistencia_pct===null?'Sin datos disponibles':String(metrics.asistencia_pct)+' %']])){const card=reportElement('div');card.append(reportElement('strong',String(value??'Sin datos disponibles')),reportElement('span',label));cards.append(card);}container.append(cards);
   if(report.report_rows>0&&(report.chart||[]).length){
     const chart=reportElement('figure',undefined,'chat-report-chart');chart.append(reportElement('figcaption','Distribución de observaciones registradas'));
     const values=report.chart.filter(item=>Number.isFinite(item.value));const maximum=Math.max(1,...values.map(item=>item.value));
     for(const item of report.chart){const line=reportElement('div',undefined,'chat-report-bar-row');line.append(reportElement('span',item.label));
       if(Number.isFinite(item.value)){const meter=document.createElement('meter');meter.min=0;meter.max=maximum;meter.value=item.value;meter.setAttribute('aria-label',item.label+': '+item.value+' '+item.unit);line.append(meter,reportElement('b',item.value+' '+item.unit));}
       else line.append(reportElement('span','Sin datos disponibles'));chart.append(line);}container.append(chart);
   }else container.append(reportElement('p',report.kind==='ml_evaluation'?'No se mezclan escalas ni se comparan métricas de pruebas diferentes.':'Sin datos disponibles','chat-report-empty'));
   function table(title,columns,rows){
     if(!rows?.length)return;
     const wrap=reportElement('div',undefined,'chat-report-table-wrap');wrap.tabIndex=0;wrap.setAttribute('aria-label',title+'; desplaza para ver todas las columnas');const grid=document.createElement('table');grid.append(reportElement('caption',title));
     const head=document.createElement('thead'),tr=document.createElement('tr');for(const [,label] of columns){const cell=reportElement('th',label);cell.scope='col';tr.append(cell);}head.append(tr);grid.append(head);
     const body=document.createElement('tbody');for(const item of rows){const tr=document.createElement('tr');for(const [key] of columns)tr.append(reportElement('td',item[key]===null?'Sin datos disponibles':String(item[key]??'')));body.append(tr);}grid.append(body);wrap.append(grid);container.append(wrap);
   }
   table(report.kind==='ml_evaluation'?'Resultados ML archivados':'Vista previa de registros',report.columns||[],report.rows);
   table('Comparación entre períodos',[['periodo','Período'],['registros','Registros'],['presentes','Presentes'],['tardanzas','Tardanzas'],['ausencias','Ausencias'],['asistencia_pct','Asistencia (%)']],report.comparison);
   table('Calificaciones disponibles',[['curso','Curso'],['estudiante','Estudiante'],['evaluaciones','Evaluaciones'],['promedio_ponderado','Promedio ponderado (0–20)']],report.grades);
   const details=reportElement('details');details.append(reportElement('summary','Metodología y vencimiento'),reportElement('p',report.methodology),reportElement('p','Este reporte temporal vence en 10 minutos. Los archivos requieren la misma cuenta y permisos vigentes.'));container.append(details);
   const actions=reportElement('div',undefined,'chat-report-actions');const reportStatus=reportElement('p','Revisa esta vista previa antes de descargar.','chat-report-status');reportStatus.setAttribute('role','status');
   for(const [format,label] of [['xlsx','Descargar Excel'],['pdf','Descargar PDF'],['docx','Descargar Word'],['print','Imprimir PDF']]){
     const button=reportElement('button',label);button.type='button';if(report.requested_formats?.includes(format))button.className='requested';
     button.onclick=()=>downloadReport(report,format,button,reportStatus);actions.append(button);
   }
   container.append(actions,reportStatus);row.querySelector('.bubble').append(container);
   requestAnimationFrame(()=>{const top=feed.scrollTop+row.getBoundingClientRect().top-feed.getBoundingClientRect().top;feed.scrollTo({top:Math.max(0,top),behavior:'instant'});});
 }
 async function downloadReport(report,format,button,output){
   const print=format==='print';const fmt=print?'pdf':format;let tab=null;
   if(print){tab=window.open('about:blank','_blank');if(!tab){output.textContent='Permite la pestaña emergente para abrir e imprimir el PDF, o usa Descargar PDF.';return;}tab.opener=null;tab.document.body.textContent='Preparando PDF autorizado…';}
   button.disabled=true;output.textContent='Preparando '+fmt.toUpperCase()+'…';
   try{
     const file=await api('/api/chatbot/reports/'+encodeURIComponent(report.id)+'/exports/'+fmt,{method:'POST'});
     // La URL no lleva tokens. La descarga vuelve a usar el encabezado autenticado.
     if(file.url!=='/api/chatbot/reports/'+report.id+'/files/'+fmt)throw Error('Ruta de descarga no válida.');
     const response=await Auth.fetchAutenticado(file.url);
     if(!response.ok){const error=await response.json().catch(()=>({}));throw Error(typeof error.detail==='string'?error.detail:'No se pudo descargar el reporte.');}
     const url=URL.createObjectURL(await response.blob());
     if(print){tab.location.replace(url+'#toolbar=1');tab.focus();output.textContent='PDF abierto: usa el icono Imprimir o Ctrl+P en esa pestaña.';setTimeout(()=>URL.revokeObjectURL(url),600000);}
     else {const anchor=document.createElement('a');anchor.href=url;anchor.download=file.filename;document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);output.textContent='Archivo '+fmt.toUpperCase()+' descargado.';}
   }catch(error){tab?.close();output.textContent=error.message;}finally{button.disabled=false;}
 }
 function renderHistory(){
  const list=$('chat-history-list');list.replaceChildren();
  if(!historyEntries.length){const li=document.createElement('li');li.textContent='Todavía no tienes consultas guardadas.';list.append(li);return;}
  for(const item of [...historyEntries].reverse()){
   const li=document.createElement('li'),button=document.createElement('button');button.type='button';button.textContent=item.question;
   button.onclick=()=>{input.value=item.question;input.focus();status.textContent='Pregunta del historial seleccionada. Revísala y pulsa Enviar.';};li.append(button);list.append(li);
  }
 }
 async function loadHistory(){try{historyEntries=await api('/api/chatbot/history');for(const row of historyEntries){add('user',row.question);add('assistant',row.reply);}renderHistory();}catch(e){status.textContent=e.message;}}
 async function refreshNotifications(){
  try{const rows=await api('/api/chatbot/proactive/notifications');if(!Array.isArray(rows))return;const count=rows.filter(n=>n.state==='unread').length;
   for(const id of ['chat-notification-count','chat-launch-count']){const badge=$(id);badge.hidden=count===0;badge.textContent=count?String(count):'';}
   $('chat-notifications').setAttribute('aria-label','Recordatorios y notificaciones'+(count?', '+count+' sin leer':''));
  }catch{/* Sin datos disponibles no se inventa un contador. */}
 }
 function open(){
  if(!panel.hidden)return;lastFocus=document.activeElement;pageScroll=window.scrollY;
  backgroundStates=[...surface.children].filter(el=>el!==host&&!['SCRIPT','STYLE','LINK','ASIDE'].includes(el.tagName)).map(el=>[el,el.inert]);
  for(const [el] of backgroundStates){el.inert=true;el.setAttribute('data-chat-suspended','');}
  surface.classList.add('monitor-chat-surface');document.body.classList.add('monitor-chat-active');
  panel.hidden=false;$('chat-launch').setAttribute('aria-expanded','true');viewport();window.scrollTo?.(0,0);
  if(!historyPromise)historyPromise=loadHistory();refreshNotifications();input.focus();
 }
 function cancelVoice(){if(!listening)return;cancelled=true;recognition.abort();input.value=originalDraft;status.textContent='Audio cancelado. No se envió la pregunta.';}
 function close(){
  cancelVoice();stopSpeaking();controls();$('chat-mic-consent').hidden=true;panel.hidden=true;$('chat-launch').setAttribute('aria-expanded','false');
  for(const [el,inert] of backgroundStates){el.inert=inert;el.removeAttribute('data-chat-suspended');}
  backgroundStates=[];surface.classList.remove('monitor-chat-surface');document.body.classList.remove('monitor-chat-active');
  window.scrollTo?.(0,pageScroll);lastFocus?.focus?.({preventScroll:true});window.dispatchEvent(new Event('resize'));
 }
 function openNotifications(){
  close();if(window.monitorProactive){window.monitorProactive.open();return;}
  const role=user.rol==='ESTUDIANTE'?'estudiante':'profesor';
  location.href=new URL('../'+role+'/ia.html#notificaciones',scriptUrl).href;
 }
 $('chat-launch').onclick=open;$('chat-close').onclick=close;$('chat-menu').onclick=()=>window.PanelNavigation?.open($('chat-menu'));
 $('chat-notifications').onclick=openNotifications;document.querySelectorAll('[data-open-chat]').forEach(b=>b.onclick=open);
 $('chat-history').onclick=async()=>{
  const area=$('chat-history-panel');area.hidden=!area.hidden;$('chat-history').setAttribute('aria-expanded',String(!area.hidden));
  if(!area.hidden){$('chat-history-list').replaceChildren(reportElement('li','Cargando historial autorizado…'));try{historyEntries=await api('/api/chatbot/history');renderHistory();area.scrollIntoView?.({block:'start'});}catch(e){status.textContent=e.message;}}
 };
 $('chat-history-clear').onclick=()=>{$('chat-history-confirm').hidden=false;$('chat-history-delete').focus();};
 $('chat-history-cancel').onclick=()=>{$('chat-history-confirm').hidden=true;};
 $('chat-history-delete').onclick=async()=>{if(busy||listening)return;busy=true;controls();try{await api('/api/chatbot/history',{method:'DELETE'});historyEntries=[];renderHistory();$('chat-history-confirm').hidden=true;status.textContent='Historial guardado eliminado. La conversación abierta sigue visible hasta iniciar una nueva.';}catch(e){status.textContent=e.message;}finally{busy=false;controls();}};
 panel.addEventListener('keydown',e=>{if(e.key==='Escape'&&!document.body.classList.contains('panel-nav-open')){e.preventDefault();close();}});
 async function send(source='text'){
   if(busy||listening)return;if(historyPromise)await historyPromise;if(busy||listening)return;
   const text=input.value.trim();if(!text)return;if(text.length>2000){status.textContent='La pregunta debe tener hasta 2000 caracteres.';return;}
   stopSpeaking();busy=true;controls();add('user',text,source==='voice'?'Transcrito desde tu voz':'');input.value='';input.style.height='auto';status.textContent='Consultando tus datos…';const pending=add('assistant','Consultando…');
   const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),30000);
   const submittedChanges={...selectionChanges};
   try{const data=await api('/api/chatbot/message',{method:'POST',signal:controller.signal,body:JSON.stringify({message:text,source,context_token:conversationToken,...submittedChanges})});pending.remove();selectionChanges={};applyContext(data.context);lastReply=data.reply;const answerRow=add('assistant',data.reply,data.demo?'Datos ficticios · '+data.provider:'Consulta · '+data.provider);if(data.report)showReport(answerRow,data.report);if(data.ml)showML(answerRow,data.ml);if(data.proactive){const go=reportElement("button","Ir al centro de notificaciones");go.type="button";go.onclick=openNotifications;answerRow.querySelector(".bubble").append(go);}status.textContent=data.notice||'';readReply(lastReply);}
   catch(e){pending.remove();add('assistant',e.name==='AbortError'?'La consulta tardó demasiado. Puedes volver a intentarlo.':e.status===401?'Tu sesión ha expirado. Vuelve a iniciar sesión para consultar tus datos.':e.message);input.value=text;if(e.status===409){resetContext();status.textContent='Se restableció el contexto. Revisa tus filtros y reenvía la pregunta.';}else status.textContent='Puedes revisar la pregunta y volver a enviarla.';}
   finally{clearTimeout(timer);busy=false;controls();input.focus();}
 }
 $('chat-form').onsubmit=e=>{e.preventDefault();send();};input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();send();}});
 host.querySelectorAll('.suggestion').forEach(b=>b.onclick=()=>{input.value=b.dataset.question||b.textContent;send();});
 $('chat-new').onclick=async()=>{if(busy||listening)return;stopSpeaking();busy=true;controls();try{
  if(historyPromise)await historyPromise;messages.replaceChildren();resetContext();lastReply='';$('chat-welcome').hidden=false;
  $('chat-history-panel').hidden=true;$('chat-history').setAttribute('aria-expanded','false');status.textContent='Nueva conversación. Tus consultas anteriores siguen disponibles en Historial.';input.value='';
 }catch(e){status.textContent=e.message;}finally{busy=false;controls();input.focus();}};
 const Speech=window.SpeechRecognition||window.webkitSpeechRecognition;
 if(!Speech){$('voice-hint').textContent='Voz no disponible en este navegador';status.textContent='Este navegador no admite voz; puedes escribir tu pregunta.';mic.disabled=true;mic.title='Este navegador no admite reconocimiento de voz';}else if(!window.isSecureContext){$('voice-hint').textContent='La voz necesita HTTPS o localhost';status.textContent='Para usar el micrófono, abre el sitio con HTTPS o localhost.';mic.disabled=true;}else{
 recognition=new Speech();recognition.lang='es-PE';recognition.continuous=false;recognition.interimResults=true;recognition.maxAlternatives=1;
 recognition.onstart=()=>{status.textContent='Escuchando… Al terminar de hablar se enviará la transcripción.';};
 recognition.onresult=e=>{let interim='';finalTranscript='';for(let i=0;i<e.results.length;i++){const text=e.results[i][0].transcript;if(e.results[i].isFinal)finalTranscript+=text+' ';else interim+=text+' ';}input.value=(finalTranscript+interim).trim();};
 recognition.onerror=e=>{failed=true;const errors={'not-allowed':'Permite el micrófono en el navegador y vuelve a intentarlo.','service-not-allowed':'El servicio de voz no está disponible. Puedes escribir tu pregunta.','no-speech':'No se detectó voz. Inténtalo nuevamente.','audio-capture':'No se encontró un micrófono disponible.','network':'No se pudo conectar con el servicio de voz. Revisa tu conexión.','aborted':'Audio cancelado.'};if(!cancelled)status.textContent=errors[e.error]||'No se pudo transcribir el audio. Puedes escribir tu pregunta.';};
 recognition.onend=()=>{listening=false;controls();if(!cancelled&&!failed&&finalTranscript.trim()){input.value=finalTranscript.trim();status.textContent='Transcripción lista. Enviando consulta…';send('voice');}else if(!cancelled&&!failed){status.textContent='No se obtuvo una transcripción. Puedes volver a intentar.';}input.focus();};
 function startListening(){
   if(busy||ttsActive)return;
   if(Date.now()<micBlockedUntil){status.textContent='Espera un instante después del audio y vuelve a pulsar el micrófono.';return;}
   $('chat-mic-consent').hidden=true;cancelled=false;failed=false;finalTranscript='';originalDraft=input.value;listening=true;controls();
   try{recognition.start();}catch{listening=false;controls();status.textContent='No se pudo iniciar el micrófono. Inténtalo nuevamente.';}
 }
 mic.onclick=()=>{if(busy||ttsActive)return;if(listening){recognition.stop();status.textContent='Terminando transcripción…';return;}if(!micConsent){$('chat-mic-consent').hidden=false;$('chat-mic-allow').focus();return;}startListening();};
 $('chat-mic-allow').onclick=()=>{micConsent=true;micBlockedUntil=0;startListening();};
 $('chat-mic-deny').onclick=()=>{$('chat-mic-consent').hidden=true;status.textContent='Puedes continuar escribiendo. No se activó el micrófono.';input.focus();};
 $('voice-cancel').onclick=cancelVoice;window.addEventListener('pagehide',()=>{cancelled=true;recognition.abort();});
 }
 // Mantiene la desactivación del micrófono en navegadores sin soporte.
 const baseControls=controls;controls=()=>{baseControls();if(!Speech||!window.isSecureContext)mic.disabled=true;};
 window.addEventListener('pagehide',()=>{stopSpeaking();conversationToken=null;selectionChanges={};synthesis?.removeEventListener?.('voiceschanged',populateVoices);});
 controls();refreshNotifications();
 window.monitorChat={open,close,previewReport:report=>{open();const row=add("assistant","Reporte programado: revisa la vista previa antes de descargar.");showReport(row,report);},setCourse:id=>{$('chat-course').value=String(id);selectionChanges.course_id=Number(id);selectionChanges.student_id=null;$('chat-student').value='';}};
 if(document.body.classList.contains('chatbot-page')&&!location.hash.includes('notificaciones'))open();
 document.dispatchEvent(new Event('monitor:chat-ready'));
})();
