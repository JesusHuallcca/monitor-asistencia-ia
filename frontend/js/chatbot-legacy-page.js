/* Adaptador de presentación para la página de asistencia heredada.
   No cambia capturas, permisos, consentimiento ni llamadas del componente de cámara. */
'use strict';
(async()=>{
 if(!Auth.token())return;
 // camera.js declara API_URL como URL del check-in; Auth requiere el origen de API.
 const base=localStorage.getItem('API_URL')||(location.pathname.startsWith('/frontend/')?location.origin:API_URL.replace(/\/api\/attendance\/camera\/check-in\/?$/,''));
 Auth.fetchAutenticado=(path,options={})=>fetch(base+path,{...options,headers:{...options.headers,Authorization:'Bearer '+Auth.token()}});
 document.body.classList.add('admin-page');document.body.dataset.rol='estudiante';
 const page=document.querySelector('.page');if(!page)return;
 const css=document.createElement('link');css.rel='stylesheet';css.href='../css/admin.css';document.head.append(css);
 const layout=document.createElement('div');layout.className='admin-layout';
 const aside=document.createElement('aside');aside.className='admin-menu';page.before(layout);layout.append(aside,page);page.classList.add('admin-principal');
 await Panel.iniciar('estudiante');
})();
