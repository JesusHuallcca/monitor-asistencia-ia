"use strict";
(() => {
 const $=id=>document.getElementById(id); let report=null; let demo=false;
 const fmt=(n,d=3)=>n==null?'No disponible':Number(n).toLocaleString('es-PE',{maximumFractionDigits:d,minimumFractionDigits:d});
 const status=(text,error=false)=>{$('status').textContent=text;$('status').classList.toggle('error',error)};
 async function api(path,options={}){
   const base=window.Parte6System?.base ?? (demo?'':API_URL);
   const headers={'Content-Type':'application/json',...(Auth.token()?{Authorization:'Bearer '+Auth.token()}:{})};
   const response=await fetch(base+'/api/parte6'+path,{...options,headers,credentials:demo?'include':'omit'});
   const data=await response.json().catch(()=>({}));
   if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:response.status===422?'Revisa los valores y las fechas del historial.':'No autorizado o datos no disponibles ('+response.status+').');
   return data;
 }
 const config={responsive:true,displayModeBar:'hover',displaylogo:false,modeBarButtonsToRemove:['toImage','select2d','lasso2d','autoScale2d'],scrollZoom:false};
 function plot(id,traces,layout={}){return Plotly.react(id,traces,{font:{family:'Segoe UI',size:11,color:'#46617e'},margin:{l:50,r:20,t:20,b:50},paper_bgcolor:'white',plot_bgcolor:'white',hoverlabel:{bgcolor:'#092b53',font:{color:'white',size:11}},legend:{orientation:'h',y:1.15},...layout},config)}
 function text(tag,value,cls){const el=document.createElement(tag);el.textContent=value;if(cls)el.className=cls;return el}
 const featureLabels={asistencia_30d:'Asistencia en los últimos 30 días',tardanzas_30d:'Tardanzas en los últimos 30 días',asistencia_ultimas5:'Asistencia en las últimas 5 sesiones',sesiones_previas:'Cantidad de sesiones previas',promedio_previo:'Promedio de notas ya disponibles',sin_notas:'Indicador de ausencia de notas',dia_sin:'Día de la semana · seno',dia_cos:'Día de la semana · coseno',hora:'Hora programada de la sesión'};
 function renderArchitecture(r){
   const stage=$('architecture'),detail=$('nn-detail'),tooltip=$('nn-tooltip');
   stage.replaceChildren();tooltip.hidden=true;
   const layers=[{units:r.features.length,activation:'Historial previo',parameters:0},...r.architecture];
   const svgNS='http://www.w3.org/2000/svg';
   function svgNode(name,attributes){const node=document.createElementNS(svgNS,name);Object.entries(attributes).forEach(([key,value])=>node.setAttribute(key,value));return node}
   const links=svgNode('svg',{viewBox:'0 0 1000 300',preserveAspectRatio:'none','aria-hidden':'true',class:'nn-links'});
   for(let gap=0;gap<layers.length-1;gap++){
     const group=svgNode('g',{'data-gap':gap});
     for(let j=0;j<7;j++){
       const x=175+gap*250,y=92+j*19,end=106+(6-j)*15;
       group.append(svgNode('path',{d:`M ${x} ${y} C ${x+70} ${y}, ${x+80} ${end}, ${x+150} ${end}`}));
     }
     links.append(group);
   }
   stage.append(links);
   const buttons=[];
   const layerName=i=>i===0?'Entrada':i===layers.length-1?'Salida':'Capa oculta '+i;
   const descriptions=layers.map((l,i)=>i===0?'Recibe las variables históricas disponibles antes de la sesión objetivo. Los identificadores y la asistencia que se quiere predecir quedan fuera de las entradas.':i===layers.length-1?'Combina la representación de la última capa oculta. La activación sigmoide produce la probabilidad estimada de asistir a la siguiente sesión; no es una certeza sobre el estudiante.':i===1?'Aprende combinaciones no lineales de asistencia, puntualidad, notas y calendario. Cada neurona calcula una suma ponderada con sesgo y aplica ReLU: máximo entre cero y ese valor.':'Combina las señales aprendidas en la capa anterior en una representación más compacta antes de calcular la salida. ReLU mantiene las respuestas positivas y convierte las negativas en cero.');
   function variableList(){const list=text('ul','','nn-features');r.features.forEach(f=>{const item=text('li','');item.append(text('span',featureLabels[f]||f),text('code',f));list.append(item)});return list}
   function hideTooltip(){tooltip.hidden=true;buttons.forEach(b=>b.removeAttribute('aria-describedby'))}
   function showTooltip(i){tooltip.replaceChildren(text('strong',layerName(i)+' · '+layers[i].units+(i===0?' variables':' neuronas')));if(i===0)tooltip.append(variableList());else tooltip.append(text('p',(i===layers.length-1?'Sigmoide: probabilidad de asistencia. ':'ReLU: ')+(i===1?'aprende combinaciones de los antecedentes.':i===2?'refina las señales de la capa anterior.':'')));tooltip.hidden=false;buttons[i].setAttribute('aria-describedby','nn-tooltip')}
   function select(i){
     buttons.forEach((b,k)=>b.setAttribute('aria-pressed',String(k===i)));
     links.querySelectorAll('g').forEach((g,k)=>g.classList.toggle('is-active',k===i||k===i-1));
     detail.dataset.layer=i;detail.style.setProperty('--layer-color',`var(--nn-color-${Math.min(i,3)})`);
     const heading=text('h3',layerName(i),'');heading.id='nn-detail-title';
     detail.replaceChildren(text('span','CAPA '+(i+1)+' / '+layers.length,'nn-detail-step'),heading,text('p',descriptions[i]));
     if(i===0)detail.append(variableList());
     else{
       const info=text('div','','nn-detail-facts');
       info.append(text('span',layers[i].units+' '+(layers[i].units===1?'neurona':'neuronas')),text('span','Activación: '+(layers[i].activation==='relu'?'ReLU':'sigmoide')),text('span',layers[i].parameters.toLocaleString('es-PE')+' parámetros'));
       detail.append(info);
       detail.append(text('p',`Parámetros = (${layers[i-1].units} entradas + 1 sesgo) × ${layers[i].units} neuronas = ${layers[i].parameters}.`,'nn-formula'));
     }
     hideTooltip();
   }
   layers.forEach((layer,i)=>{
     const button=text('button','','layer nn-layer');button.type='button';button.dataset.layer=i;button.setAttribute('aria-controls','nn-detail');button.setAttribute('aria-pressed','false');
     button.setAttribute('aria-label',layerName(i)+': '+layer.units+(i===0?' variables':layer.units===1?' neurona':' neuronas')+', '+(i===0?'historial previo':layer.activation==='relu'?'ReLU':'sigmoide'));
     button.style.setProperty('--layer-color',`var(--nn-color-${Math.min(i,3)})`);
     button.append(text('span',String(i+1).padStart(2,'0'),'nn-step'),text('span',layerName(i),'nn-layer-name'));
     const amount=text('span','','nn-amount');amount.append(text('strong',layer.units),text('span',i===0?'variables':layer.units===1?'neurona':'neuronas'));button.append(amount);
     const nodes=svgNode('svg',{viewBox:'0 0 120 166',class:'nn-neurons','aria-hidden':'true'});
     const columns=i===0?3:layer.units===1?1:4,rows=Math.ceil(layer.units/columns);
     for(let n=0;n<layer.units;n++){
       const col=n%columns,row=Math.floor(n/columns),cx=columns===1?60:25+col*70/(columns-1),cy=rows===1?80:19+row*128/(rows-1);
       nodes.append(svgNode('circle',{cx,cy,r:layer.units===1?15:i===0?7:5,class:'nn-neuron'}));
     }
     button.append(nodes,text('span',i===0?'Datos históricos':layer.activation==='relu'?'ReLU · max(0, z)':'Sigmoide · 0 a 1','nn-activation'));
     button.addEventListener('click',()=>select(i));
     button.addEventListener('pointerenter',e=>{if(e.pointerType==='mouse' && window.matchMedia('(hover: hover) and (pointer: fine)').matches)showTooltip(i)});
     button.addEventListener('pointerleave',hideTooltip);
     button.addEventListener('focus',()=>{if(button.matches(':focus-visible'))showTooltip(i)});
     button.addEventListener('blur',hideTooltip);
     button.addEventListener('keydown',e=>{if(e.key==='Escape')hideTooltip()});
     buttons.push(button);stage.append(button);
   });
   $('nn-summary').replaceChildren(...[[r.features.length,'entradas'],[r.architecture.length-1,'capas ocultas'],[r.architecture.at(-1).units,'salida'],[r.parameters,'parámetros entrenables']].map(([n,label])=>{const card=text('div','','nn-stat');card.append(text('strong',n.toLocaleString('es-PE')),text('span',label));return card}));
   select(0);
 }
 async function render(r){
   report=r;$('content').hidden=false;
   $('ntrain').textContent=r.splits[0].rows.toLocaleString('es-PE');$('ntest').textContent=r.splits[2].rows.toLocaleString('es-PE');$('auc').textContent=fmt(r.metrics.neuronal.roc_auc);$('epoch').textContent=r.best_epoch+' / '+r.history.loss.length;
   $('params').textContent=r.parameters.toLocaleString('es-PE')+' parámetros entrenables';
   renderArchitecture(r);
   const epochs=r.history.loss.map((_,i)=>i+1);
   const m=r.metrics.neuronal,b=r.metrics.logistica;
   await Promise.all([
    plot('loss',[{x:epochs,y:r.history.loss,name:'Entrenamiento',mode:'lines',line:{color:'#0754b5',width:3}},{x:epochs,y:r.history.val_loss,name:'Validación',mode:'lines',line:{color:'#db8a24',width:3}}],{xaxis:{title:'Época',dtick:Math.max(1,Math.ceil(epochs.length/8))},yaxis:{title:'Entropía cruzada binaria'}}),
    plot('confusion',[{type:'heatmap',x:['No asiste','Asiste'],y:['No asiste','Asiste'],z:m.confusion_matrix,colorscale:[[0,'#edf4fd'],[1,'#0754b5']],showscale:false,text:m.confusion_matrix.map(row=>row.map(String)),texttemplate:'%{text}',hovertemplate:'Real: %{y}<br>Predicho: %{x}<br>Sesiones: %{z}<extra></extra>'}],{xaxis:{title:'Predicción'},yaxis:{title:'Resultado real',autorange:'reversed'}}),
    plot('comparison',[{type:'bar',x:['Accuracy','Precision','Recall','F1','ROC-AUC'],y:[m.accuracy,m.precision,m.recall,m.f1,m.roc_auc],name:'Red neuronal',marker:{color:'#0754b5'}},{type:'bar',x:['Accuracy','Precision','Recall','F1','ROC-AUC'],y:[b.accuracy,b.precision,b.recall,b.f1,b.roc_auc],name:'Regresión logística',marker:{color:'#40a4a0'}}],{barmode:'group',yaxis:{range:[0,1.05],title:'Métrica (0–1)'}})
   ]);
   const names={accuracy:'Accuracy',precision:'Precision',recall:'Recall',f1:'F1',roc_auc:'ROC-AUC',brier:'Brier ↓',log_loss:'Log loss ↓'};
   $('metrics').replaceChildren(...Object.entries(names).map(([key,label])=>{const tr=document.createElement('tr');tr.append(text('th',label),text('td',fmt(m[key])),text('td',fmt(b[key])));return tr}));
   const delta=m.roc_auc-b.roc_auc;$('conclusion').textContent='En esta prueba sintética, '+(Math.abs(delta)<.001?'los ROC-AUC son similares.':delta>0?'la red obtiene mayor ROC-AUC.':'la regresión logística obtiene mayor ROC-AUC.')+' Esta comparación no evalúa el modelo histórico del proyecto ni demuestra superioridad en estudiantes reales.';
   $('example').replaceChildren(...r.examples.map((ex,i)=>{const opt=text('option',ex.student_id+' · '+ex.session_at.replace('T',' '));opt.value=i;return opt}));
   $('splits').replaceChildren(...r.splits.map(s=>{const el=text('div','','split');el.append(text('strong',s.name+': '+s.rows+' sesiones · '+s.students+' perfiles'),text('p',s.start.slice(0,10)+' · '+s.end.slice(0,10)));return el}));
   $('provenance').textContent='Semilla '+r.seed+' · Python '+r.versions.python+' · TensorFlow '+r.versions.tensorflow+' · Keras '+r.versions.keras+(r.model_info?' · Modelo '+r.model_info.model_version:'')+' · SHA-256 del dataset: '+r.dataset_sha256;
 }
 async function load(){ $('refresh').disabled=true;try{status('Leyendo resultados del entrenamiento real…');await render(await api('/report'));status('Resultados cargados · datos sintéticos · umbral de clasificación 0,5.');$('activate').hidden=true}catch(e){status(e.message,true)}finally{$('refresh').disabled=false}}
 $('activate').addEventListener('click',async()=>{try{await api('/demo/session',{method:'POST'});await load()}catch(e){status(e.message,true)}});
 $('refresh').addEventListener('click',load);
 $('predictform').addEventListener('submit',async e=>{e.preventDefault();if(!report)return;$('predict').disabled=true;try{const ex=structuredClone(report.examples[Number($('example').value)]);if($('grade').value!==''){const grade=Number($('grade').value);if(!Number.isFinite(grade)||grade<0||grade>20)throw new Error('La nota debe estar entre 0 y 20.');ex.history.forEach(h=>{h.nota=grade})}const p=await api('/predict',{method:'POST',body:JSON.stringify({origen:'sintetico',session_at:ex.session_at,history:ex.history})});$('prediction').textContent='Probabilidad neuronal: '+fmt(100*p.probabilidad,1)+' % · Regresión logística: '+fmt(100*p.logistica_probabilidad,1)+' %. '+p.advertencia;status('Predicción calculada por el modelo guardado.')}catch(e){status(e.message,true)}finally{$('predict').disabled=false}});
 new ResizeObserver(()=>['loss','confusion','comparison'].forEach(id=>{if($(id).data)Plotly.Plots.resize($(id))})).observe(document.querySelector('main'));
 window.addEventListener('parte6-auth',load);
 (async()=>{try{const mode=await window.Parte6System.ready;demo=mode.demo===true}catch(_){}if(demo){$('activate').hidden=false;status(window.Parte6System.system?'Puedes activar la demostración sintética o autenticarte para consultar datos académicos.':'Modo local sin MySQL. Pulsa «Iniciar demostración sintética».')}else if(!Auth.token()){status('Inicia sesión con una cuenta de profesor para consultar el módulo.',true)}else await load()})();
})();
