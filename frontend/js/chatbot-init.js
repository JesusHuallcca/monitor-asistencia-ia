'use strict';
window.monitorReady=(async()=>{
 if(typeof Auth==='undefined'||!Auth.token())return null;
 const api=async(path,options={})=>{
  const r=await Auth.fetchAutenticado(path,{...options,headers:{'Content-Type':'application/json',...options.headers}});
  const d=await r.json().catch(()=>({}));
  if(!r.ok){if(r.status===401)Auth.limpiar();throw Error(typeof d.detail==='string'?d.detail:'No se pudo procesar la consulta.');}return d;
 };
 try{
  const original=await api('/api/users/me');
  if(!['estudiante','profesor','admin'].includes(original.rol))return null;
  const context=await api('/api/chatbot/context');
  const user={id_usuario:original.id,nombre:original.nombres+' '+original.apellidos,rol:({admin:'ADMIN',superadmin:'ADMIN',profesor:'PROFESOR',estudiante:'ESTUDIANTE'})[original.rol]};
  return {user,originalUser:original,context,api};
 }catch(e){console.warn('El asistente no está disponible:',e.message);const esExpired=e.message&&(e.message.includes('Token')||e.message.includes('expirad')||e.message.includes('utenticad')||e.message.includes('401'));const warning=document.createElement('p');warning.setAttribute('role','status');warning.textContent=esExpired  ?'Tu sesión ha expirado. Vuelve a iniciar sesión para usar el Asistente IA.'  :'El asistente IA no está disponible en este momento.';warning.style.cssText='position:fixed;bottom:15px;right:15px;max-width:320px;background:#fffbeb;color:#92400e;border:1px solid #fcd34d;padding:12px 16px;border-radius:12px;font:13px/1.5 Segoe UI;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,.12)';document.body.append(warning);setTimeout(()=>warning.remove(),6000);return null;}
})();
