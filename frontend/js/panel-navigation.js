/* Navegación compartida, acotada a los paneles de profesor y estudiante. */
'use strict';
(()=>{
 const scriptUrl=new URL(document.currentScript.src,location.href);
 if(document.getElementById('panel-navigation-css'))return;
 const css=document.createElement('link');css.id='panel-navigation-css';css.rel='stylesheet';css.href=new URL('../css/panel-navigation.css',scriptUrl).href;document.head.append(css);
 let trigger=null;
 const menu=()=>document.querySelector('.admin-menu,.dashboard-sidebar');
 const close=()=>{document.body.classList.remove('panel-nav-open');menu()?.classList.remove('abierto','open');document.querySelector('.admin-overlay-movil')?.classList.remove('activo');document.querySelectorAll('#panel-menu-toggle,#chat-menu').forEach(b=>b.setAttribute('aria-expanded','false'));trigger?.focus?.();};
 const open=button=>{trigger=button;menu()?.classList.remove('abierto','open');document.querySelector('.admin-overlay-movil')?.classList.remove('activo');document.body.classList.add('panel-nav-open');document.querySelectorAll('#panel-menu-toggle,#chat-menu').forEach(b=>b.setAttribute('aria-expanded','true'));menu()?.querySelector('button,a')?.focus();};
 function mount(){
  if(!['estudiante','profesor'].includes(document.body.dataset.rol)||!menu())return;
  document.body.classList.add('panel-navigation');
  const aside=menu();aside.id=aside.id||'panel-navigation';const existingClose=aside.querySelector('.btn-cerrar-drawer');existingClose?.classList.add('panel-nav-close');aside.setAttribute('aria-label','Navegación SENATI');
  if(!aside.querySelector('.panel-nav-close')){const b=document.createElement('button');b.type='button';b.className='panel-nav-close';b.setAttribute('aria-label','Cerrar menú');b.textContent='×';b.onclick=close;aside.prepend(b);}
  if(!document.getElementById('panel-menu-toggle')){const b=document.createElement('button');b.type='button';b.id='panel-menu-toggle';b.className='panel-menu-toggle';b.setAttribute('aria-label','Abrir menú de navegación');b.setAttribute('aria-controls',aside.id);b.setAttribute('aria-expanded','false');b.textContent='☰';b.onclick=()=>document.body.classList.contains('panel-nav-open')?close():open(b);document.body.append(b);}
 }
 document.addEventListener('click',e=>{
  if(!document.body.classList.contains('panel-navigation'))return;
  const button=e.target.closest('.btn-hamburguesa,.btn-cerrar-drawer,#btn-toggle-menu');
  if(!button)return;
  e.preventDefault();e.stopImmediatePropagation();
  if(button.matches('.btn-cerrar-drawer'))close();else document.body.classList.contains('panel-nav-open')?close():open(button);
 },true);
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.body.classList.contains('panel-nav-open')){e.preventDefault();e.stopImmediatePropagation();close();}},true);
 document.addEventListener('click',e=>{if(!document.body.classList.contains('panel-nav-open'))return;if(!e.target.closest('.admin-menu,#panel-menu-toggle,#chat-menu'))close();});
 window.PanelNavigation={mount,open,close};mount();
})();
