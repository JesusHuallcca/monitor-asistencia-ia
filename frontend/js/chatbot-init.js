'use strict';
window.monitorReady=(async()=>{
 if(typeof Auth==='undefined'||!Auth.token())return null;
 const api=async(path,options={})=>{
  const r=await Auth.fetchAutenticado(path,{...options,headers:{'Content-Type':'application/json',...options.headers}});
  const d=await r.json().catch(()=>({}));
  if(!r.ok){if(r.status===401)Auth.limpiar();throw Error(typeof d.detail==='string'?d.detail:'No se pudo procesar la consulta.');}return d;
 };
 try{
  const original=await api('/api/users/me');const context=await api('/api/chatbot/context');
  const user={id_usuario:original.id,nombre:original.nombres+' '+original.apellidos,rol:({admin:'ADMIN',superadmin:'ADMIN',profesor:'PROFESOR',estudiante:'ESTUDIANTE'})[original.rol]};
  return {user,originalUser:original,context,api};
 }catch(e){console.warn('El asistente no está disponible:',e.message);const warning=document.createElement('p');warning.setAttribute('role','status');warning.textContent='Asistente no disponible: '+e.message;warning.style.cssText='position:fixed;bottom:15px;right:15px;max-width:300px;background:#fff3dc;color:#72470b;border:1px solid #efcd83;padding:12px;border-radius:12px;font:13px Segoe UI;z-index:35';document.body.append(warning);return null;}
})();
