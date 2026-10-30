"use strict";
(()=>{
 const $=id=>document.getElementById(id);let mode={demo:true,system:false},requestVersion=0,available=false;
 const connection=window.Parte6System={base:'',ready:null};
 const message=(value,error=false)=>{$('system-status').textContent=value;$('system-status').classList.toggle('error',error)};
 const node=(tag,value)=>{const e=document.createElement(tag);e.textContent=value;return e};
 async function api(path,options={}){
   const response=await fetch(connection.base+'/api/parte6'+path,{...options,headers:{'Content-Type':'application/json',Authorization:'Bearer '+(Auth.token()||'')},credentials:'omit'});
   const result=await response.json().catch(()=>({}));
   if(!response.ok){const detail=result.detail;const error=new Error(typeof detail==='string'?detail:detail?.message||'Revisa la selección y los permisos de acceso.');error.status=response.status;error.blockers=detail?.blockers||[];if(response.status===401){Auth.limpiar();$('system-login').hidden=false}throw error}
   return result;
 }
 function clear(){requestVersion++;$('system-predict').disabled=true;$('system-prediction').hidden=true;$('system-detail').hidden=true;$('system-blockers').replaceChildren()}
 function options(id,rows,label,format){$(id).replaceChildren(node('option',label));$(id).firstChild.value='';for(const row of rows){const option=node('option',format(row));option.value=row.id;$(id).append(option)}$(id).disabled=!rows.length}
 function selected(){return {curso_id:Number($('system-course').value),estudiante_id:Number($('system-student').value),sesion_id:Number($('system-session').value)}}
 async function courses(){try{const rows=await api('/system/courses');options('system-course',rows,'Selecciona un curso',r=>r.codigo+' · '+r.nombre);message(rows.length?'Selecciona un curso para consultar sus estudiantes.':'No hay cursos activos asignados a este profesor.');$('system-login').hidden=true}catch(error){message(error.message,true)}}
 function showContext(data){
   $('system-detail').hidden=false;$('system-predict').disabled=!data.ready;$('system-prediction').hidden=true;
   $('system-cutoff').textContent='Origen: MySQL · Corte: '+data.cutoff.replace('T',' ')+' · Notas disponibles: '+data.grades_count;
   $('system-blockers').replaceChildren(...data.blockers.map(v=>node('p',v)));
   $('system-warnings').replaceChildren(...[data.advertencia,...data.warnings].map(v=>node('li',v)));
   const keys=['asistencia_30d','tardanzas_30d','asistencia_ultimas5','sesiones_previas','promedio_previo','sin_notas','dia_sin','dia_cos','hora'];
   $('system-features').replaceChildren(...keys.map(key=>{const box=node('div','');box.append(node('code',key),node('strong',data.features?Number(data.features[key]).toLocaleString('es-PE',{maximumFractionDigits:4}):'No disponible'));return box}));
   $('system-history').replaceChildren(...data.history.map(row=>{const tr=node('tr','');tr.append(node('td',row.sesion_id),node('td',row.session_at.replace('T',' ')),node('td',row.estado||row.motivo));return tr}));
   message(data.ready?'Historial preparado. Puedes ejecutar la inferencia experimental.':'Predicción bloqueada: faltan datos fiables. No se inventarán registros.',!data.ready);
 }
 function showError(error){message(error.message,true);$('system-blockers').replaceChildren(...(error.blockers||[]).map(v=>node('p',v)));$('system-predict').disabled=true}
 async function switchMode(system){
   $('mode-system').setAttribute('aria-pressed',String(system));$('mode-demo').setAttribute('aria-pressed',String(!system));$('system-panel').hidden=!system;$('demo-examples').hidden=system;
   $('mode-caption').textContent=system?(available?'Datos académicos · experimental':'Pendiente de integración'):'Ejemplos simulados';
   if(!system)return;
   if(!mode.system){message('Pendiente de integración: la API académica protegida debe conectarse desde el backend de tu compañero.',false);return}
   if(!available)return;
   if(!Auth.token()){$('system-login').hidden=false;message('Autentícate como profesor para consultar datos del sistema.');return}
   await courses();
 }
 $('mode-system').addEventListener('click',()=>switchMode(true));$('mode-demo').addEventListener('click',()=>switchMode(false));
 $('system-course').addEventListener('change',async()=>{
   clear();options('system-student',[],'Selecciona un estudiante',()=> '');options('system-session',[],'No consultada',()=> '');$('system-context').disabled=true;
   const id=$('system-course').value,version=requestVersion;if(!id)return;
   try{const [students,sessions]=await Promise.all([api('/system/courses/'+encodeURIComponent(id)+'/students'),api('/system/courses/'+encodeURIComponent(id)+'/sessions')]);if(version!==requestVersion)return;options('system-student',students,'Selecciona un estudiante',r=>r.codigo+' · '+r.nombre);options('system-session',sessions,'Selecciona la próxima sesión',r=>r.session_at.replace('T',' '));if(sessions.length===1)$('system-session').value=sessions[0].id;message(!students.length?'No hay estudiantes activos matriculados.':!sessions.length?'No hay próxima sesión activa programada.':'Selecciona un estudiante y consulta el historial.')}catch(error){if(version===requestVersion)showError(error)}
 });
 ['system-student','system-session'].forEach(id=>$(id).addEventListener('change',()=>{clear();$('system-context').disabled=!Object.values(selected()).every(v=>v>0)}));
 $('system-selection').addEventListener('submit',async e=>{e.preventDefault();clear();const version=requestVersion;$('system-context').disabled=true;try{const data=await api('/system/context',{method:'POST',body:JSON.stringify(selected())});if(version===requestVersion)showContext(data)}catch(error){if(version===requestVersion)showError(error)}finally{$('system-context').disabled=!Object.values(selected()).every(v=>v>0)}});
 $('system-predict').addEventListener('click',async()=>{const version=requestVersion;$('system-predict').disabled=true;$('system-prediction').hidden=true;message('Cargando el modelo y calculando la inferencia. La primera consulta puede tardar unos segundos.');try{const data=await api('/system/predict',{method:'POST',body:JSON.stringify(selected())});if(version!==requestVersion)return;showContext(data);$('system-prediction').textContent='Probabilidad experimental de asistencia: '+(data.probabilidad*100).toLocaleString('es-PE',{maximumFractionDigits:1})+' %. Modelo entrenado con datos sintéticos; no es un resultado académico validado.';$('system-prediction').hidden=false;message('Inferencia ejecutada con el modelo guardado. No se ha guardado la predicción en MySQL.')}catch(error){if(version===requestVersion)showError(error)}});
 $('system-login').addEventListener('submit',async e=>{e.preventDefault();const button=e.submitter;button.disabled=true;try{const result=await api('/auth/login',{method:'POST',body:JSON.stringify({identificador:$('system-user').value,password:$('system-password').value})});Auth.guardarSesion(result,false);$('system-login').hidden=true;await courses();window.dispatchEvent(new Event('parte6-auth'))}catch(error){showError(error)}finally{$('system-password').value='';button.disabled=false}});
 connection.ready=(async()=>{
   try{const local=['127.0.0.1','localhost'].includes(location.hostname);const candidates=[...new Set(['',API_URL,...(local?[location.protocol+'//'+location.hostname+':8007']:[])])];let response=null;
    for(const base of candidates){try{const candidate=await fetch(base+'/api/parte6/mode',{signal:AbortSignal.timeout(4000)});if(candidate.ok){const parsed=await candidate.json();if(parsed.demo!==undefined){response=parsed;connection.base=base;break}}}catch(_){}}
    if(!response)throw new Error('API no disponible');mode=response;connection.system=mode.system===true;if(mode.database_kind==='sqlite_fixture'){document.querySelector('.notice').prepend(node('strong','PRUEBA AUTOMÁTICA CON SQLITE EN MEMORIA · NO ES MYSQL. '))}
    if(mode.system){const response=await fetch(connection.base+'/api/parte6/system/status');const data=await response.json();available=data.configured;message(data.message,!available);await switchMode(true)}
   }catch(error){message('No se pudo identificar el backend de Parte 6. Revisa su configuración.',true)}
   return mode;
 })();
})();
