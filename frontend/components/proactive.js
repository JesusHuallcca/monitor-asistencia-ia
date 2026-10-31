/* Centro interno de acciones: no controla el reloj ni ejecuta trabajos programados. */
'use strict';
(async()=>{
 const scriptUrl=new URL(document.currentScript?.src||'/frontend/components/proactive.js',location.href);
 const ready=await window.monitorReady;if(!ready)return;
 const {user,context,api}=ready;
 const parent=document.querySelector('.admin-cuerpo');if(!parent)return;
 const css=document.createElement('link');css.rel='stylesheet';css.href=new URL('../css/proactive.css',scriptUrl).href;document.head.append(css);
 const root=document.createElement('section');root.id='notificaciones';root.className='proactive-center';root.tabIndex=-1;root.setAttribute('aria-labelledby','proactive-title');
 root.innerHTML=`
 <header class="proactive-heading"><div><span class="proactive-eyebrow">MONITOR IA · PARTE 7</span><h2 id="proactive-title">Centro de notificaciones y acciones</h2><p>Fechas verificadas, avisos configurables y reportes preparados por el servidor.</p></div><button type="button" id="proactive-refresh">Actualizar</button></header>
 <p class="proactive-note">Solo para tu cuenta. Cada acción necesita revisión y confirmación. No se envían mensajes a terceros ni se toman decisiones académicas automáticas.</p>
 <div id="proactive-status" role="status" aria-live="polite"></div>
 <p id="proactive-worker" role="status"></p><div id="proactive-content" hidden>
 <div class="proactive-settings"><label><input type="checkbox" id="proactive-enabled"> Habilitar recordatorios de mi cuenta</label><span>Canal: notificaciones internas</span></div>
 <section aria-labelledby="proactive-dates-title"><h3 id="proactive-dates-title">Fechas verificadas próximas</h3><div id="proactive-suggestions" class="proactive-suggestions"></div></section>
 <details class="proactive-create"><summary>Configurar un recordatorio o una acción</summary>
 <form id="proactive-form" class="proactive-form">
 <label>Acción<select name="kind" id="proactive-kind"><option value="next_class">Próxima clase</option><option value="evaluation">Evaluación con fecha</option><option value="weekly_summary">Resumen semanal de asistencia</option><option value="absence_alert">Alerta por ausencias</option><option value="tardy_alert">Alerta por tardanzas</option><option value="scheduled_report">Reporte programado del profesor</option><option value="tutoring">Tutoría declarada por mí</option><option value="meeting">Reunión declarada por mí</option><option value="communication">Borrador de comunicación académica</option></select></label>
 <label id="proactive-course-wrap">Curso<select name="course_id" id="proactive-course"><option value="">Seleccionar curso</option></select></label>
 <label id="proactive-student-wrap">Estudiante autorizado<select name="student_id" id="proactive-student"><option value="">Todo el curso autorizado</option></select></label>
 <label id="proactive-source-wrap">Fecha verificada<select name="source_id" id="proactive-source"><option value="">Seleccionar evento existente</option></select></label>
 <label>Zona horaria<input name="timezone" id="proactive-timezone" value="America/Lima" list="proactive-zones" required maxlength="64"><datalist id="proactive-zones"><option value="America/Lima"><option value="UTC"><option value="America/Bogota"></datalist></label>
 <label id="proactive-frequency-wrap">Frecuencia<select name="frequency" id="proactive-frequency"><option value="once">Una vez</option><option value="daily">Diaria</option><option value="weekly">Semanal</option></select></label>
 <label id="proactive-time-wrap">Hora local de aviso<input name="local_time" type="time" value="08:00"></label>
 <label id="proactive-day-wrap">Día<select name="weekday"><option value="0">Lunes</option><option value="1">Martes</option><option value="2">Miércoles</option><option value="3">Jueves</option><option value="4">Viernes</option><option value="5">Sábado</option><option value="6">Domingo</option></select></label>
 <label id="proactive-lead-wrap">Minutos antes<input name="reminder_minutes" type="number" min="0" max="1440" value="30"></label>
 <label id="proactive-threshold-wrap">Umbral de registros<input name="threshold" type="number" min="1" max="100" value="3"></label>
 <label id="proactive-window-wrap">Ventana de días<input name="window_days" type="number" min="1" max="90" value="30"></label>
 <label id="proactive-title-wrap">Título del evento declarado<input name="title" maxlength="140"></label>
 <label id="proactive-event-wrap">Fecha y hora con desplazamiento horario<input name="event_at" placeholder="2026-11-05T14:00:00-05:00"><small>Ejemplo ISO para Lima: -05:00. Esta fecha la proporcionas tú.</small></label>
 <label id="proactive-text-wrap">Texto propuesto, sujeto a revisión<textarea name="text" maxlength="1500" rows="3" placeholder="Propuesta de acompañamiento académico…"></textarea></label>
 <p id="proactive-form-note" class="proactive-form-note"></p><div class="proactive-form-actions"><button type="submit" id="proactive-save">Preparar para revisión</button><button type="button" id="proactive-new">Limpiar formulario</button></div>
 </form></details>
 <div class="proactive-grid"><section><h3>Notificaciones <span id="proactive-count">0</span></h3><div id="proactive-inbox"></div></section><section><h3>Mis acciones</h3><div id="proactive-actions"></div></section></div></div>`;
 parent.append(root);const $=id=>root.querySelector('#'+id),form=$('proactive-form');
 const labels={next_class:'Próxima clase',evaluation:'Evaluación',weekly_summary:'Resumen semanal',absence_alert:'Aviso de ausencias',tardy_alert:'Aviso de tardanzas',scheduled_report:'Reporte programado',tutoring:'Tutoría',meeting:'Reunión',communication:'Comunicación'};
 const frequencies={once:'Una vez',daily:'Diaria',weekly:'Semanal'};
 const states={draft:'Por revisar',active:'Activa',paused:'Pausada',blocked:'Bloqueada: revisar permisos o fuente',completed:'Completada',cancelled:'Cancelada',reviewed:'Borrador aprobado, sin envío'};
 let available=false,busy=false,editing=null,sources={classes:[],evaluations:[]},timer;
 const message=text=>$('proactive-status').textContent=text;
 function node(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
 function button(text,run){const b=node('button',text);b.type='button';b.onclick=async()=>{b.disabled=true;try{await run();}catch(e){message(e.message);}finally{b.disabled=false;}};return b;}
 function date(value,zone){if(!value)return 'Sin ejecución programada';try{return new Intl.DateTimeFormat('es-PE',{dateStyle:'medium',timeStyle:'short',timeZone:zone||'America/Lima'}).format(new Date(value));}catch{return value;}}
 for(const c of context.courses){const o=node('option',c.nombre);o.value=c.id;$('proactive-course').append(o);}
 if(user.rol!=='PROFESOR'){for(const value of ['scheduled_report','communication'])$('proactive-kind').querySelector('option[value="'+value+'"]').remove();}
 if(user.rol==='ESTUDIANTE')$('proactive-student-wrap').hidden=true;
 async function students(){
  const course=Number($('proactive-course').value);$('proactive-student').replaceChildren(node('option','Todo el curso autorizado'));$('proactive-student').firstChild.value='';
  if(!course||user.rol==='ESTUDIANTE')return;
  const values=await api('/api/chatbot/proactive/students?course_id='+course);
  for(const item of values){const option=node('option',item.name);option.value=item.id;$('proactive-student').append(option);}
 }
 function fillSources(){
  const kind=$('proactive-kind').value,course=Number($('proactive-course').value),select=$('proactive-source');select.replaceChildren(node('option','Seleccionar evento existente'));select.firstChild.value='';
  const values=(kind==='next_class'?sources.classes:sources.evaluations).filter(v=>v.course_id===course);
  for(const item of values){const o=node('option',kind==='next_class'?date(item.event_at):item.name+' · '+item.date+' (sin hora de vencimiento)');o.value=item.id;select.append(o);}
 }
 function fields(reset=false){
  const kind=$('proactive-kind').value,manual=['tutoring','meeting'].includes(kind),alert=['absence_alert','tardy_alert'].includes(kind),recur=['weekly_summary','scheduled_report',...['absence_alert','tardy_alert']].includes(kind);
  if(reset)$('proactive-frequency').value=kind==='weekly_summary'||kind==='scheduled_report'?'weekly':alert?'daily':'once';
  for(const [id,show] of [['source',kind==='next_class'||kind==='evaluation'],['lead',kind==='next_class'||manual],['time',recur||kind==='evaluation'],['day',recur&&$('proactive-frequency').value==='weekly'],['threshold',alert],['window',alert],['title',manual],['event',manual],['text',kind==='communication'],['frequency',recur]])$('proactive-'+id+'-wrap').hidden=!show;
  $('proactive-form-note').textContent=manual?'La tutoría o reunión se registra como declarada por ti; no se atribuye a MySQL.':kind==='evaluation'?'El esquema contiene una fecha DATE. La hora elegida es la del aviso, no una hora inventada de vencimiento.':kind==='communication'?'Se preparará un borrador con datos autorizados. Aprobarlo no envía mensajes.':'Los reportes usan períodos cerrados; las alertas cuentan solo registros explícitos. Destinatario: mi cuenta.';
  fillSources();
 }
 $('proactive-kind').onchange=()=>fields(true);$('proactive-frequency').onchange=()=>fields();
 $('proactive-course').onchange=async()=>{fillSources();try{await students();}catch(e){message(e.message);}};
 function reset(){editing=null;form.reset();$('proactive-save').textContent='Preparar para revisión';fields(true);}
 $('proactive-new').onclick=reset;
 async function act(action,operation){
  const value=await api('/api/chatbot/proactive/actions/'+action.id+'/transition',{method:'POST',body:JSON.stringify({version:action.version,operation,confirmed:operation==='activate'||operation==='review'})});
  message(operation==='review'?'Borrador aprobado para revisión humana; no se ha enviado.':'Estado actualizado: '+states[value.status]);await load();
 }
 async function edit(action){
  if(!action.config){message('El ámbito cambió. Crea una nueva acción con tus permisos actuales.');return;}
  editing=action;const spec=action.config.spec;form.reset();
  for(const [key,value] of Object.entries(spec))if(form.elements.namedItem(key)&&value!==null)form.elements.namedItem(key).value=String(value);
  fields();await students();$('proactive-student').value=spec.student_id||'';fillSources();$('proactive-source').value=spec.source_id||'';
  root.querySelector('.proactive-create').open=true;$('proactive-save').textContent='Guardar cambios para revisión';form.scrollIntoView({block:'start',behavior:'smooth'});
 }
 function renderSuggestions(data){
  const area=$('proactive-suggestions');area.replaceChildren();
  const items=[...data.classes.map(v=>({...v,kind:'next_class',order:v.event_at})),...data.evaluations.map(v=>({...v,kind:'evaluation',order:v.date}))].sort((a,b)=>a.order.localeCompare(b.order)).slice(0,4);
  if(!items.length){area.append(node('p','No hay fechas verificadas próximas en tu ámbito.','proactive-empty'));return;}
  for(const item of items){
   const card=node('article',undefined,'proactive-suggestion');const course=context.courses.find(c=>c.id===item.course_id)?.nombre||'Curso autorizado';
   card.append(node('strong',item.kind==='next_class'?'Próxima clase · '+course:'Evaluación · '+course),node('p',item.kind==='next_class'?date(item.event_at):item.name+' · '+item.date+' (sin hora de vencimiento)'));
   card.append(button(item.kind==='next_class'?'Preparar aviso de clase':'Preparar aviso de evaluación',async()=>{
    reset();$('proactive-kind').value=item.kind;$('proactive-course').value=String(item.course_id);fields(true);await students();fillSources();$('proactive-source').value=String(item.id);root.querySelector('.proactive-create').open=true;
    message('Fecha verificada seleccionada. Revisa la configuración; todavía no se creó ni activó ningún recordatorio.');form.scrollIntoView({behavior:'smooth',block:'center'});$('proactive-source').focus({preventScroll:true});
   }));area.append(card);
  }
 }
 function renderActions(values){
  const area=$('proactive-actions');area.replaceChildren();
  if(!values.length)area.append(node('p','No tienes acciones. El asistente no programa nada sin tu confirmación.','proactive-empty'));
  for(const a of values){
   const card=node('article',undefined,'proactive-card');card.dataset.actionId=a.id;card.append(node('h4',a.config?.spec.title||a.title),node('span',states[a.status]||a.status,'proactive-state'));
   card.append(node('p','Destinatario: '+a.recipient+' · '+(frequencies[a.frequency]||a.frequency)+' · '+a.timezone),node('p',date(a.next_run,a.timezone)));
   if(a.config){const d=node('details');d.append(node('summary','Revisar configuración y fuente'));
    d.append(node('p',a.config.source.description));
    if(a.config.source.event_at)d.append(node('p','Evento: '+date(a.config.source.event_at,a.timezone)));
    if(a.config.source.date)d.append(node('p','Fecha verificada: '+a.config.source.date+'; no se dispone de hora de vencimiento.'));
    if(a.config.spec.title)d.append(node('p',a.config.spec.title));
    if(a.config.draft_text){const text=node('textarea');text.readOnly=true;text.rows=7;text.value=a.config.draft_text;text.setAttribute('aria-label','Borrador sin enviar');d.append(text);}
    d.append(node('p','Frecuencia: '+a.frequency+' · Zona: '+a.timezone+' · Solo esta cuenta.'));card.append(d);}
   const controls=node('div',undefined,'proactive-card-actions');
   if(!['completed','cancelled','reviewed'].includes(a.status)){
    if(['draft','paused','blocked'].includes(a.status))controls.append(button(a.kind==='communication'?'Aprobar borrador (sin envío)':'Activar recordatorio',()=>act(a,a.kind==='communication'?'review':'activate')));
    if(a.status==='active')controls.append(button('Pausar',()=>act(a,'pause')));
    controls.append(button('Editar',()=>edit(a)),button('Cancelar',()=>act(a,'cancel')),button('Marcar completada',()=>act(a,'complete')));
   }
   card.append(controls);area.append(card);
  }
 }
 function renderInbox(values){
  const area=$('proactive-inbox');area.replaceChildren();$('proactive-count').textContent=String(values.filter(n=>n.state==='unread').length);
  if(!values.length)area.append(node('p','No hay notificaciones disponibles.','proactive-empty'));
  for(const n of values){
   const card=node('article',undefined,'proactive-card');card.dataset.notificationId=n.id;card.append(node('h4',n.title),node('p',n.message),node('small',date(n.created_at)+' · '+({unread:'No leída',read:'Leída',completed:'Completada'}[n.state]||n.state)));
   if(n.source?.event_at)card.append(node('p','Evento: '+date(n.source.event_at)));
   if(n.source?.date)card.append(node('p','Fecha de vencimiento: '+n.source.date+' (sin hora verificada)'));
   const controls=node('div',undefined,'proactive-card-actions');
   if(n.has_report)controls.append(button('Ver reporte y descargar',async()=>{const report=await api('/api/chatbot/proactive/notifications/'+n.id+'/report',{method:'POST'});window.monitorChat?.previewReport(report);}));
   for(const [state,label] of [['read','Marcar leída'],['completed','Completar']])if(n.state!==state)controls.append(button(label,async()=>{await api('/api/chatbot/proactive/notifications/'+n.id,{method:'PATCH',body:JSON.stringify({state})});await load();}));
   card.append(controls);area.append(card);
  }
 }
 async function load(){
  if(busy||!available)return;busy=true;
  try{const [p,a,n,s,w]=await Promise.all(['/preferences','/actions','/notifications','/sources','/status'].map(path=>api('/api/chatbot/proactive'+path)));$('proactive-enabled').checked=p.enabled;$('proactive-worker').textContent=w.worker_running?'Planificador del servidor activo.':'Planificador sin actividad reciente: las acciones quedan en espera hasta iniciar el worker.';sources=s;renderSuggestions(s);renderActions(a);renderInbox(n);}
  catch(e){message(e.message);}finally{busy=false;}
 }
 form.onsubmit=async e=>{
  e.preventDefault();if(busy)return;const data=new FormData(form),kind=data.get('kind');
  const spec={kind,course_id:data.get('course_id')?Number(data.get('course_id')):null,student_id:data.get('student_id')?Number(data.get('student_id')):null,timezone:data.get('timezone'),frequency:data.get('frequency'),local_time:data.get('local_time')||'08:00',weekday:Number(data.get('weekday')),reminder_minutes:Number(data.get('reminder_minutes')),threshold:Number(data.get('threshold')),window_days:Number(data.get('window_days')),title:data.get('title')||'',text:data.get('text')||''};
  if(['next_class','evaluation'].includes(kind)){if(!data.get('source_id')){message('Selecciona una fecha verificada del curso.');return;}spec.source_id=Number(data.get('source_id'));}
  if(['tutoring','meeting'].includes(kind))spec.event_at=data.get('event_at');
  if(!['tutoring','meeting'].includes(kind)&&!spec.course_id){message('Selecciona un curso autorizado.');return;}
  $('proactive-save').disabled=true;
  try{const a=await api('/api/chatbot/proactive/actions'+(editing?'/'+editing.id:''),{method:editing?'PUT':'POST',body:JSON.stringify(editing?{version:editing.version,spec}:spec)});message(a.status==='draft'?'Borrador preparado. Revisa la fuente y pulsa Activar recordatorio o Aprobar borrador.':'Ya existe esta acción. Estado: '+(states[a.status]||a.status)+'. No se creó otra.');editing=null;await load();$('proactive-actions').scrollIntoView({block:'start',behavior:'smooth'});}
  catch(error){message(error.message);}finally{$('proactive-save').disabled=false;}
 };
 $('proactive-enabled').onchange=async()=>{try{await api('/api/chatbot/proactive/preferences',{method:'PUT',body:JSON.stringify({enabled:$('proactive-enabled').checked,timezone:$('proactive-timezone').value})});message($('proactive-enabled').checked?'Recordatorios habilitados.':'Recordatorios desactivados para esta cuenta.');}catch(e){message(e.message);await load();}};
 $('proactive-refresh').onclick=load;
 try{const state=await api('/api/chatbot/proactive/status');available=state.available;message(state.message);$('proactive-content').hidden=!available;if(available){fields(true);await load();timer=setInterval(()=>{if(!document.hidden)load();},15000);}}
 catch(e){message('Centro no disponible: '+e.message);}
 window.monitorProactive={open:()=>{root.scrollIntoView({behavior:'smooth',block:'start'});root.focus({preventScroll:true});},refresh:load};
 if(location.hash==='#notificaciones')window.monitorProactive.open();
 window.addEventListener('pagehide',()=>clearInterval(timer));
})();