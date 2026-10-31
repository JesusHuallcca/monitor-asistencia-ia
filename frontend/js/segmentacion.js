/* Plotly local. Solo datos de la API sintética; sin cambios al ajuste K-Means. */
document.addEventListener('DOMContentLoaded', async () => {
  const $ = (id) => document.getElementById(id);
  const features = ['asistencia_ratio','tardanzas_ratio','promedio_notas','expresiones_positivas_ratio'];
  const labels = ['Asistencia','Tardanzas','Promedio de notas','Expresiones positivas sintéticas'];
  const colors = ['#f43f5e','#6366f1','#10b981','#06b6d4','#f59e0b','#8b5cf6','#ec4899','#38bdf8'];
  const categoryIds = ['neutral','alegria','sorpresa','tristeza','enojo','disgusto','miedo','desprecio'];
  const categoryColumns = [...categoryIds.map(id => 'exp_sint_'+id),'exp_sint_total','exp_sint_origen'];
  const required = ['usuario_id','estado','promedio_notas','origen_datos'];
  const allowed = new Set([...required,...categoryColumns,'sesion','sesion_id','curso_id','fecha','asistencia_ratio_30d','asistencias_consecutivas',
    'ausencias_consecutivas','dia_semana','hora_inicio_clase','es_inicio_ciclo','tardanzas_ratio','asistira','perfil',
    // Columnas de salida del modelo (se ignoran en la validación del cliente)
    'segmento','cluster','pca_1','pca_2','asistencia_ratio','expresiones_positivas_ratio','silueta','grupo','etiqueta']);
  const chartIds = ['seg-pca','seg-comparison','seg-expresiones-scatter','seg-distribution','seg-bar-asistencia','seg-bar-tardanzas','seg-bar-notas','seg-bar-expresiones','seg-expression-chart'];
  const fmt = (value, digits = 2) => Number(value).toLocaleString('es-PE',{maximumFractionDigits:digits});
  const percent = (value) => fmt(value * 100,1) + ' %';
  const number = fmt;
  const color = (id) => colors[(id - 1) % colors.length];
  const isRatio = (field) => field.endsWith('_ratio');
  const label = (field) => labels[features.indexOf(field)];
  const axisLabel = (field) => field === 'expresiones_positivas_ratio' ? 'Expresiones sintéticas' : label(field);
  const value = (point, field) => point[field] * (isRatio(field) ? 100 : 1);
  let result = null, valid = false, validationVersion = 0, busy = false, epoch = 0, viewVersion = 0, renderTicket = 0;
  let hiddenGroups = new Set(), selectedIds = new Set(), renderQueue = Promise.resolve();
  function error(message = '') { $('seg-error').textContent = message; $('seg-error').hidden = !message; }
  function clearResults() {
    epoch++; renderTicket++; $('seg-results').setAttribute('aria-busy','false'); result = null; hiddenGroups.clear(); selectedIds.clear();
    $('seg-expression-detail').hidden = true; $('seg-expression-total').textContent = ''; $('seg-expression-note').textContent = '';
    $('seg-download').disabled = true; $('seg-filter').disabled = true; $('seg-results').hidden = true; $('seg-empty').hidden = false; $('seg-selection').hidden = true;
    for (const id of chartIds) { hideTooltip($(id)); if (window.Plotly && $(id).data) Plotly.purge($(id)); $(id)._segBound = false; $(id)._segDragMode = 'zoom'; $(id).replaceChildren(); }
    for (const id of ['seg-count','seg-k','seg-score','seg-variables']) $(id).textContent = '—';
    $('seg-groups').replaceChildren(); $('seg-selection-body').replaceChildren();
    $('seg-filter').replaceChildren(new Option('Todos',''));
    $('seg-visible').textContent = '';
    for (const id of ['seg-distribution-note','seg-pca-note','seg-comparison-note','seg-expresiones-note','seg-choice-note','seg-choice-title']) $(id).textContent = '';
  }
  try { if (!await Panel.iniciar('profesor')) return; }
  catch { error('No se pudo verificar tu sesión. Revisa la conexión con el backend local.'); $('seg-status').textContent = 'Conexión con el servidor pendiente.'; return; }
  if (!window.Plotly) { error('No se pudo cargar la biblioteca local de gráficos. Recarga la página.'); return; }
  $('seg-demo').disabled = false; $('seg-status').textContent = 'Elige la demostración o carga sesiones sintéticas.';
  // Lectura de la cabecera respetando comillas CSV. La validación de cada fila es del servidor.
  function header(text) {
    const first = text.replace(/^\uFEFF/, '').split(/\r?\n/, 1)[0];
    if (!first || first.length > 4096) throw new Error('La cabecera está vacía o es demasiado larga.');
    const fields = [];
    let i = 0;
    while (i < first.length) {
      let value = '';
      if (first[i] === '"') {
        i++;
        let closed = false;
        while (i < first.length) {
          if (first[i] === '"') {
            if (first[i + 1] === '"') { value += '"'; i += 2; }
            else { i++; closed = true; break; }
          } else value += first[i++];
        }
        if (!closed || (i < first.length && first[i] !== ',')) throw new Error('Comillas inválidas en la cabecera.');
      } else {
        while (i < first.length && first[i] !== ',') value += first[i++];
      }
      fields.push(value);
      if (first[i] === ',') { i++; if (i === first.length) fields.push(''); }
    }
    return fields;
  }
  $('seg-file').addEventListener('change', async () => {
    if (busy) return;
    const version = ++validationVersion;
    // panel cerrado
    valid = false;
    error(); clearResults(); $('seg-process').disabled = true;
    const file = $('seg-file').files[0];
    $('seg-file-info').textContent = file ? file.name + ' · ' + number(file.size / 1024, 1) + ' KiB' : 'Ningún archivo seleccionado.';
    if (!file) { $('seg-status').textContent = 'Selecciona un CSV para comenzar.'; return; }
    try {
      if (!/\.csv$/i.test(file.name)) throw new Error('Selecciona un archivo con extensión .csv.');
      if (!file.size || file.size > 2 * 1024 * 1024) throw new Error('El CSV debe contener datos y no superar 2 MiB.');
      const text = new TextDecoder('utf-8', { fatal: true }).decode(await file.arrayBuffer());
      if (version !== validationVersion) return;
      const columns = header(text);
      if (new Set(columns).size !== columns.length) throw new Error('La cabecera contiene columnas duplicadas.');
      // Detección: ¿Es CSV de perfiles/resultados exportados (sin columna 'estado')?
      const isProfileCsv = !columns.includes('estado') && columns.includes('usuario_id') && columns.includes('promedio_notas');
      if (!isProfileCsv) {
        const missing = required.filter((name) => !columns.includes(name));
        if (missing.length) throw new Error('Faltan columnas obligatorias: ' + missing.join(', ') + '.');
        if (columns.filter((name) => ['sesion', 'sesion_id'].includes(name)).length !== 1)
          throw new Error('Incluye exactamente una columna: sesion o sesion_id.');
      }
      if (columns.some(name => categoryColumns.includes(name)) && !categoryColumns.every(name => columns.includes(name)))
        throw new Error('Detalle categórico incompleto: incluye las ocho categorías, exp_sint_total y exp_sint_origen.');
      const unknown = columns.filter((name) => !allowed.has(name));
      // Columnas desconocidas se ignoran (el servidor las filtra)
      // if (unknown.length) throw new Error(...)  <-- ya no se rechaza
      valid = true;
      const rows = text.trimEnd().split(/\r?\n/).length - 1;
      $('seg-status').textContent = 'Archivo "' + file.name + '" (' + number(rows, 0) + ' registros) validado. Procesando segmentación...';
      setTimeout(() => process('csv'), 60);
      const labelTipo = isProfileCsv ? 'perfiles de estudiantes' : 'registros de sesión';
      $('seg-file-info').textContent += ' · ' + number(rows, 0) + ' ' + labelTipo;
      $('seg-status').textContent = 'Cabecera válida. Al procesar se comprobarán los valores y el origen sintético de todas las filas.';
    } catch (e) {
      if (version !== validationVersion) return;
      error(e instanceof TypeError ? 'No se pudo leer el CSV en UTF-8.' : e.message);
      $('seg-status').textContent = 'Revisa el archivo antes de procesar.';
    }
    $('seg-process').disabled = !valid || busy;
  });
  for (const name of ['dragover', 'dragleave', 'drop']) $('seg-drop').addEventListener(name, (event) => {
    event.preventDefault();
    $('seg-drop').classList.toggle('seg-drag', name === 'dragover');
    if (name === 'drop' && !busy) {
      if (event.dataTransfer.files.length !== 1) { error('Arrastra un único archivo CSV.'); return; }
      $('seg-file').files = event.dataTransfer.files;
      $('seg-file').dispatchEvent(new Event('change'));
    }
  });


  const config = {responsive:true,displaylogo:false,displayModeBar:'hover',scrollZoom:true,showTips:false,locale:'es',
    modeBarButtons:[['zoom2d','pan2d']]};
  const baseLayout = () => ({
    autosize:true, paper_bgcolor:'transparent', plot_bgcolor:'#ffffff',
    font:{family:'Segoe UI, Arial, sans-serif',size:12,color:'#52627b'},
    margin:{l:54,r:12,t:54,b:52}, hovermode:'closest',
    hoverlabel:{bgcolor:'#0f172a',bordercolor:'#334155',font:{family:'Segoe UI, -apple-system, sans-serif',size:11,color:'#ffffff'}},
    legend:{orientation:'h',x:0,y:1.02,yanchor:'bottom',font:{size:10},itemsizing:'constant',itemdoubleclick:false},
    uirevision:epoch + '-' + viewVersion,
    xaxis:{gridcolor:'#edf1f7',zeroline:false,automargin:true},
    yaxis:{gridcolor:'#edf1f7',zeroline:false,automargin:true},
  });
  const groupVisible = (id) => (!$('seg-filter').value || Number($('seg-filter').value) === id) && !hiddenGroups.has(id);
  const visiblePoints = () => result ? result.puntos.filter((p) => groupVisible(p.segmento)) : [];
  function refreshCounts() {
    if (!result) return;
    const visible = visiblePoints();
    const available = new Set(visible.map((p) => p.usuario_id));
    selectedIds = new Set([...selectedIds].filter((id) => available.has(id)));
    $('seg-visible').textContent = fmt(visible.length,0) + ' de ' + fmt(result.metricas.perfiles,0) + ' perfiles en grupos visibles';
    $('seg-selection').hidden = !selectedIds.size;
    $('seg-selection-count').textContent = fmt(selectedIds.size,0) + ' perfiles seleccionados';
    $('seg-selection-body').replaceChildren();
    for (const p of visible.filter((p) => selectedIds.has(p.usuario_id)).slice(0,12)) {
      const row = document.createElement('tr');
      for (const text of [p.usuario_id,'E'+p.segmento,percent(p.asistencia_ratio),percent(p.tardanzas_ratio),fmt(p.promedio_notas),percent(p.expresiones_positivas_ratio)]) {
        const cell = document.createElement('td'); cell.textContent = text; row.appendChild(cell);
      }
      $('seg-selection-body').appendChild(row);
    }
  }
  function groupDescription(id) {
    const group = result.clusters.find(g => g.segmento === id);
    const values = result.clusters.map(g => g.asistencia_ratio);
    const low = Math.min(...values), high = Math.max(...values);
    if (high-low < 1e-6) return {full:'Asistencia similar',short:'Similar'};
    if (Math.abs(group.asistencia_ratio-low) < 1e-6) return {full:'Asistencia baja',short:'Baja'};
    if (Math.abs(group.asistencia_ratio-high) < 1e-6) return {full:'Asistencia relativamente alta',short:'Alta relativa'};
    return {full:'Asistencia intermedia',short:'Intermedia'};
  }
  function chooseGroup(id) { $('seg-filter').value = String(id); hiddenGroups.clear(); selectedIds.clear(); redraw(); }
  // Fixed space below the drawing: never covers points or escapes the card.
  const tooltipNumber = (n,digits) => Number(n).toLocaleString('es-ES',{
    minimumFractionDigits:digits,maximumFractionDigits:digits
  });
  function inspector(gd) {
    if (gd._segInspector) return gd._segInspector;
    const slot = document.createElement('div'); slot.className = 'seg-point-inspector'+(gd.id === 'seg-samples' ? ' seg-silhouette-inspector' : '');
    const hint = document.createElement('span'); hint.className = 'seg-point-hint';
    hint.textContent = 'Acerca el puntero o pulsa un punto para ver su perfil.';
    const tip = document.createElement('div'); tip.className = 'seg-point-tooltip';
    tip.id = gd.id+'-tooltip'; tip.setAttribute('role','tooltip'); tip.hidden = true;
    slot.append(hint,tip); gd.insertAdjacentElement('afterend',slot);
    gd._segInspector = {slot,hint,tip};
    return gd._segInspector;
  }
  function hideTooltip(gd) {
    if (!gd._segInspector) return;
    gd._segInspector.tip.hidden = true; gd._segInspector.tip.replaceChildren();
    gd._segInspector.hint.hidden = false; gd.removeAttribute('aria-describedby');
  }
  function showTooltip(gd,point) {
    if (!result || !point?.customdata) return;
    const centroid = !!point.data?.meta?.centroide;
    const p = centroid ? result.centroides.find(g => g.segmento === point.data.meta.segmento) : result.puntos.find(p => String(p.usuario_id) === String(point.customdata[0]));
    if (!p || !groupVisible(p.segmento)) return;
    const {tip,hint} = inspector(gd);
    tip.replaceChildren();
    const heading = document.createElement('strong');
    heading.textContent = (centroid ? 'Centroide' : 'Perfil '+p.usuario_id)+' · Grupo E'+p.segmento;
    const dot = document.createElement('span'); dot.className = 'seg-tooltip-dot';
    dot.style.backgroundColor = color(p.segmento); heading.prepend(dot); tip.append(heading);
    for (const [name,field,digits] of [
      ['Asistencia','asistencia_ratio',1],['Tardanzas','tardanzas_ratio',1],
      ['Nota media','promedio_notas',2],['Expresiones sintéticas','expresiones_positivas_ratio',1]
    ]) {
      const line = document.createElement('div');
      line.textContent = name+': '+tooltipNumber(value(p,field),digits)+(isRatio(field) ? ' %' : '');
      tip.append(line);
    }
    if (gd.id === 'seg-samples' && !centroid) {
      const score = result.siluetas.find(s => s.usuario_id === p.usuario_id);
      const line = document.createElement('div'); line.textContent = 'Silueta: '+tooltipNumber(score.silueta,4); tip.append(line);
    }
    tip.hidden = false; hint.hidden = true; gd.setAttribute('aria-describedby',tip.id);
  }
  function bindChart(gd, scatter) {
    if (gd._segBound) return;
    if (scatter) {
      inspector(gd);
      gd.on('plotly_hover',event => showTooltip(gd,event.points?.[0]));
      gd.on('plotly_unhover',() => hideTooltip(gd));
    }
    gd._segBound = true;
    if (!gd._segPointerHook) {
      gd.addEventListener('mouseleave',() => hideTooltip(gd));
      gd.addEventListener('pointerdown', () => { hideTooltip(gd); gd._segUserSelection = ['select','lasso'].includes(gd._fullLayout?.dragmode); }, true);
      gd._segPointerHook = true;
    }
    gd.on('plotly_relayout', (event) => { hideTooltip(gd); if (event.dragmode) gd._segDragMode = event.dragmode; });
    gd.on('plotly_legendclick', (event) => {
      const id = gd.data[event.curveNumber]?.meta?.segmento;
      if (id !== undefined) { hiddenGroups.has(id) ? hiddenGroups.delete(id) : hiddenGroups.add(id); selectedIds.clear(); redraw(); return false; }
    });
    gd.on('plotly_legenddoubleclick', () => false);
    gd.on('plotly_click', (event) => {
      if (!result || !event.points?.length) return;
      if (scatter) {
        if (event.points[0].data.meta?.centroide) { chooseGroup(event.points[0].data.meta.segmento); return; }
        const id = event.points[0].customdata[0];
        selectedIds = new Set([id]); redraw().then(() => showTooltip(gd,event.points[0]));
      } else if (event.points[0].data.meta?.segmento) chooseGroup(event.points[0].data.meta.segmento);
    });
    if (scatter) gd.on('plotly_selected', (event) => {
      const userSelection = gd._segUserSelection;
      gd._segUserSelection = false;
      if (gd._segRendering || !userSelection) return; // Solo una interaccion del usuario cambia la seleccion.
      selectedIds = new Set((event?.points || []).map((p) => p.customdata?.[0]).filter(id => id !== null && id !== undefined)); redraw();
    });
  }
  async function plot(id, traces, layout = {}, scatter = false) {
    const stamp = epoch, gd = $(id);
    hideTooltip(gd);
    gd._segRendering = true;
    try { await Plotly.react(gd,traces,{...baseLayout(),...layout},config); }
    finally { gd._segRendering = false; }
    if (stamp !== epoch || !result) { Plotly.purge(gd); gd._segBound = false; return; }
    bindChart(gd,scatter);
  }
  function bounds(values) {
    const low = Math.min(...values), high = Math.max(...values), padding = (high-low || 1)*.08;
    return [low-padding,high+padding];
  }
  function scatterTraces(xField, yField) {
    return result.clusters.map((group) => {
      const points = result.puntos.filter((p) => p.segmento === group.segmento);
      return {type:'scatter',mode:'markers',name:'E'+group.segmento+' · '+groupDescription(group.segmento).short,legendgroup:'E'+group.segmento,meta:{segmento:group.segmento},
        x:points.map((p) => value(p,xField)),y:points.map((p) => value(p,yField)),
        ids:points.map((p) => String(p.usuario_id)),visible:groupVisible(group.segmento) ? true : 'legendonly',
        marker:{color:color(group.segmento),size:9,opacity:.88,line:{color:'#ffffff',width:1.5}},
        selectedpoints:selectedIds.size ? points.flatMap((p,i) => selectedIds.has(p.usuario_id) ? [i] : []) : null,
        selected:{marker:{opacity:1,size:11}},unselected:{marker:{opacity:.18}},
        customdata:points.map((p) => [p.usuario_id,'E'+p.segmento,percent(p.asistencia_ratio),percent(p.tardanzas_ratio),fmt(p.promedio_notas),percent(p.expresiones_positivas_ratio)]),
        hoverinfo:'none',hovertemplate:null};
    });
  }
  async function scatter(id, xField, yField, pca = false) {
    const layout = baseLayout();
    layout.dragmode = $(id)._segDragMode || 'zoom'; layout.clickmode = 'event';
    layout.uirevision += '-' + xField + '-' + yField;
    layout.xaxis = {...layout.xaxis,title:{text:pca ? 'PC1 ('+percent(result.metricas.varianza_pca[0])+')' : axisLabel(xField)},
      range:pca ? bounds(result.puntos.map((p) => p[xField])) : [0,isRatio(xField) ? 100 : 20],ticksuffix:isRatio(xField) ? ' %' : ''};
    layout.yaxis = {...layout.yaxis,title:{text:pca ? 'PC2 ('+percent(result.metricas.varianza_pca[1])+')' : axisLabel(yField)},
      range:pca ? bounds(result.puntos.map((p) => p[yField])) : [0,isRatio(yField) ? 100 : 20],ticksuffix:isRatio(yField) ? ' %' : ''};
    const traces = scatterTraces(xField,yField);
    if (pca) for (const c of result.centroides) traces.push({
      type:'scatter',mode:'markers',name:'Centroide E'+c.segmento,legendgroup:'E'+c.segmento,
      showlegend:false,meta:{segmento:c.segmento,centroide:true},visible:groupVisible(c.segmento) ? true : 'legendonly',
      x:[c.pca_1],y:[c.pca_2],customdata:[[null]],hoverinfo:'none',hovertemplate:null,
      marker:{symbol:'diamond',size:18,color:color(c.segmento),line:{color:'#ffffff',width:2.5}}
    });
    await plot(id,traces,layout,true);
  }
  async function bars(id, field, title, max) {
    const isMini = id.startsWith('seg-bar-');
    const traces = result.clusters.map((p) => ({
      type: 'bar',
      name: 'E' + p.segmento,
      meta: { segmento: p.segmento },
      x: ['E' + p.segmento],
      y: [value(p, field)],
      marker: {
        color: color(p.segmento),
        cornerradius: isMini ? 6 : 8,
        line: { color: '#ffffff', width: 2 },
        opacity: 0.92
      },
      visible: groupVisible(p.segmento) ? true : 'legendonly',
      text: [field === 'perfiles' ? fmt(p[field], 0) : isRatio(field) ? percent(p[field]) : fmt(p[field])],
      textposition: 'outside',
      cliponaxis: false,
      textfont: { family: 'Segoe UI, -apple-system, sans-serif', size: isMini ? 10 : 12, color: '#1e293b' },
      hovertemplate: '<b>%{x}</b><br>' + title + ': <b>%{y:.2f}' + (isRatio(field) ? ' %' : '') + '</b><extra></extra>'
    }));
    const layout = baseLayout();
    layout.showlegend = false;
    layout.barmode = 'stack';
    layout.bargap = isMini ? 0.32 : 0.40;
    layout.bargroupgap = 0.05;
    layout.margin = isMini ? { l: 28, r: 8, t: 24, b: 24 } : { l: 48, r: 16, t: 28, b: 40 };
    layout.xaxis = {
      ...layout.xaxis,
      title: isMini ? { text: '' } : { text: 'Cluster', font: { size: 11, color: '#64748b' } },
      type: 'category',
      categoryorder: 'array',
      categoryarray: result.clusters.map((p) => 'E' + p.segmento),
      tickfont: { size: isMini ? 10 : 11, color: '#475569' }
    };
    // Headroom para que el texto outside nunca se corte en la parte superior
    const yMax = isMini ? (isRatio(field) ? 120 : (field === 'promedio_notas' ? 24 : max * 1.25)) : max * 1.25;
    layout.yaxis = {
      ...layout.yaxis,
      title: isMini ? { text: '' } : { text: field === 'expresiones_positivas_ratio' ? 'Expresiones sintéticas' : title, font: { size: 11, color: '#64748b' } },
      range: [0, yMax],
      ticksuffix: isRatio(field) ? ' %' : '',
      tickfont: { size: isMini ? 9 : 10, color: '#64748b' },
      ...(field === 'perfiles' ? { dtick: Math.max(1, Math.ceil(max / 5)) } : {})
    };
    if (isMini) { layout.font = { size: 10 }; }
    await plot(id, traces, layout);
  }
  function renderGroups() {
    $('seg-groups').replaceChildren();
    const groups = result.clusters.filter((p) => groupVisible(p.segmento));
    if (!groups.length) { $('seg-groups').textContent = 'No hay grupos visibles. Restablece la vista para mostrarlos.'; return; }
    for (const p of groups) {
      const card = document.createElement('div'); card.className = 'seg-group'; card.style.setProperty('--cluster',color(p.segmento));
      const button = document.createElement('button'); button.type = 'button'; button.textContent = 'E'+p.segmento+' — '+groupDescription(p.segmento).full;
      button.setAttribute('aria-pressed',String($('seg-filter').value === String(p.segmento)));
      button.addEventListener('click',() => chooseGroup(p.segmento)); card.appendChild(button);
      const description = document.createElement('p');
      description.textContent = p.perfiles+' perfiles · Asistencia media '+tooltipNumber(p.asistencia_ratio*100,2)+' %'+' · tardanzas '+percent(p.tardanzas_ratio)+
        ' · nota media '+tooltipNumber(p.promedio_notas,2)+' / 20 · expresiones sintéticas '+percent(p.expresiones_positivas_ratio)+'.';
      card.appendChild(description); $('seg-groups').appendChild(card);
    }
  }
  async function sampleSilhouette() {
    let offset = 0; const ticks = [], names = [];
    const traces = result.clusters.map(group => {
      const points = result.siluetas.filter(p => p.segmento === group.segmento).sort((a,b) => a.silueta-b.silueta);
      const y = points.map((_,i) => offset+i);
      ticks.push(offset+(points.length-1)/2); names.push('E'+group.segmento);
      offset += points.length+4;
      return {type:'bar',orientation:'h',name:'E'+group.segmento,meta:{segmento:group.segmento},
        visible:groupVisible(group.segmento) ? true : 'legendonly',
        x:points.map(p => p.silueta),y,customdata:points.map(p => [p.usuario_id]),
        marker:{color:color(group.segmento)},hoverinfo:'none',hovertemplate:null};
    });
    const layout = baseLayout(); layout.showlegend = false; layout.bargap = .03;
    layout.margin = {l:38,r:14,t:36,b:46};
    layout.xaxis = {...layout.xaxis,title:{text:'Coeficiente de silueta'},range:[-1,1],dtick:.5};
    layout.yaxis = {...layout.yaxis,title:{text:'Grupo'},tickvals:ticks,ticktext:names,range:[offset,-4],showgrid:false};
    layout.shapes = [{type:'line',xref:'x',yref:'paper',x0:result.metricas.silueta,x1:result.metricas.silueta,y0:0,y1:1,line:{color:'#b91c1c',dash:'dash',width:1.5}}];
    layout.annotations = [{xref:'paper',yref:'paper',x:1,y:1.1,text:'Media: '+fmt(result.metricas.silueta,4),showarrow:false,font:{size:10,color:'#b91c1c'}}];
    await plot('seg-samples',traces,layout,true);
  }
  async function heatmap() {
    const groups = result.centroides.filter(c => groupVisible(c.segmento));
    const maximum = Math.max(1,...result.centroides.flatMap(c => c.valores_estandarizados.map(Math.abs)));
    const layout = baseLayout(); layout.showlegend = false; layout.margin = {l:36,r:45,t:30,b:58};
    layout.xaxis = {...layout.xaxis,type:'category',side:'bottom',tickangle:0,tickfont:{size:10},showgrid:false};
    layout.yaxis = {...layout.yaxis,type:'category',autorange:'reversed',showgrid:false};
    layout.annotations = groups.length ? [] : [{xref:'paper',yref:'paper',x:.5,y:.5,text:'No hay grupos visibles',showarrow:false}];
    await plot('seg-heatmap',[{type:'heatmap',x:['Asistencia','Tardanzas','Notas','Expresiones<br>sintéticas'],
      y:groups.map(c => 'E'+c.segmento),z:groups.map(c => c.valores_estandarizados),
      zmin:-maximum,zmax:maximum,zmid:0,colorscale:[[0,'#2166ac'],[.5,'#f7f9fc'],[1,'#c76c13']],
      xgap:3,ygap:3,texttemplate:'%{z:.2f}',textfont:{size:11},hoverongaps:false,
      colorbar:{title:{text:'z',side:'top'},thickness:9,len:.8,tickfont:{size:9},xpad:3},
      hovertemplate:'<b>%{y} · %{x}</b><br>Centroide estandarizado: %{z:.3f}<extra></extra>'
    }],layout);
  }
  async function evaluation() {
    const rows = result.evaluacion_k, m = result.metricas;
    const best = rows.find(p => p.k === m.k_mejor_global);
    $('seg-choice-title').textContent = '¿Por qué se eligió K='+m.clusters+'?';
    $('seg-choice-note').textContent = 'Mayor silueta entre K ≥ 3: '+fmt(m.silueta,6)+'. Mejor K global: '+m.k_mejor_global+
      ' ('+fmt(best.silueta,4)+'). Codo orientativo: '+(m.k_codo === null ? 'no concluyente' : 'K='+m.k_codo)+
      '. La silueta mide separación: '+fmt(m.silueta,4)+' no es un porcentaje de precisión.';
    const layout = baseLayout(); layout.showlegend = false; layout.margin = {l:52,r:14,t:36,b:52};
    layout.xaxis = {...layout.xaxis,title:{text:'Número de clusters (K)'},tickmode:'array',tickvals:rows.map(p => p.k)};
    layout.yaxis = {...layout.yaxis,title:{text:'Inercia'}};
    layout.shapes = [{type:'line',xref:'x',yref:'paper',x0:m.clusters,x1:m.clusters,y0:0,y1:1,line:{color:'#b91c1c',dash:'dash',width:1.5}}];
    layout.annotations = [{xref:'paper',yref:'paper',x:1,y:1.1,text:'K elegido: '+m.clusters,showarrow:false,font:{color:'#b91c1c',size:10}}];
    await plot('seg-elbow',[{type:'scatter',mode:'lines+markers',x:rows.map(p => p.k),y:rows.map(p => p.inercia),
      line:{color:'#2563eb',width:2},marker:{size:7},hovertemplate:'K=%{x}<br>Inercia: %{y:.4f}<extra></extra>'}],layout);
    $('seg-elbow-note').textContent = 'La inercia suma distancias cuadradas al centro de cada grupo. Buscar un cambio de pendiente ayuda a explorar K; el codo no decide por sí solo.';
  }
  async function expressionDistribution() {
    const detail = result.expresiones_categoricas;
    $('seg-expression-detail').hidden = !detail;
    if (!detail) return;
    const groups = detail.por_cluster.filter(g => groupVisible(g.segmento));
    const total = groups.reduce((n,g) => n+g.total_observaciones,0);
    const labels = detail.categorias.map(c => c.nombre);
    const palette = ['#64748b','#f59e0b','#8b5cf6','#ea580c','#ef4444','#0d9488','#a855f7','#ec4899'];
    const layout = baseLayout(); layout.margin = {l:58,r:16,t:45,b:56}; layout.showlegend = false;
    layout.uirevision += '-exp-'+$('seg-expression-scope').value;
    layout.yaxis = {...layout.yaxis,title:{text:'Observaciones simuladas'},rangemode:'tozero'};
    layout.xaxis = {...layout.xaxis,title:{text:'Categoría sintética'},type:'category',tickfont:{size:10}};
    let traces;
    if ($('seg-expression-scope').value === 'cluster') {
      layout.showlegend = true; layout.barmode = 'stack'; layout.margin.t = 90;
      layout.xaxis = {...layout.xaxis,title:{text:'Cluster'},type:'category',autorange:true};
      layout.yaxis = {...layout.yaxis,type:'linear',autorange:false,range:[0,Math.max(1,...groups.map(g => g.total_observaciones))*1.12]};
      traces = detail.categorias.map((category,i) => ({
        type:'bar',name:category.nombre,x:groups.map(g => 'E'+g.segmento),
        y:groups.map(g => g.conteos[category.id]),marker:{color:palette[i]},
        customdata:groups.map(g => [g.conteos[category.id]*100/g.total_observaciones,g.total_observaciones]),
        hovertemplate:'<b>%{x} · '+category.nombre+'</b><br>%{y} observaciones simuladas<br>%{customdata[0]:.2f} % de %{customdata[1]} observaciones<extra></extra>'
      }));
    } else {
      const counts = detail.categorias.map(c => groups.reduce((n,g) => n+g.conteos[c.id],0));
      traces = [{type:'bar',orientation:'h',x:counts,y:labels,marker:{color:palette},
        customdata:counts.map(n => [total ? n*100/total : 0,total]),
        text:counts.map(n => fmt(n,0)+' · '+fmt(total ? n*100/total : 0,1)+' %'),textposition:'outside',cliponaxis:false,
        hovertemplate:'<b>%{y}</b><br>%{x} observaciones simuladas<br>%{customdata[0]:.2f} % de %{customdata[1]} observaciones<extra></extra>'}];
      layout.margin = {l:85,r:16,t:30,b:48};
      layout.yaxis = {...layout.yaxis,title:{text:''},type:'category',autorange:'reversed'};
      layout.xaxis = {...layout.xaxis,title:{text:'Observaciones simuladas'},type:'linear',range:[0,Math.max(1,...counts)*1.65]};
    }
    layout.annotations = total ? [] : [{xref:'paper',yref:'paper',x:.5,y:.5,text:'No hay observaciones en los grupos visibles',showarrow:false}];
    $('seg-expression-total').textContent = fmt(total,0)+' observaciones simuladas en los grupos visibles';
    $('seg-expression-note').textContent = detail.convencion+' Los porcentajes usan el total de observaciones de la vista general o de cada cluster, no el número de perfiles. Los colores de este gráfico representan categorías, no clusters.';
    await plot('seg-expression-chart',traces,layout);
  }
  function validateExpressionDetail(data) {
    const d = data.expresiones_categoricas;
    if (d === null || d === undefined) return;
    const invalid = () => { throw new Error('El detalle de expresiones sintéticas no es válido. No se mostrarán resultados anteriores.'); };
    if (d.origen !== 'sintetico' || typeof d.convencion !== 'string' || d.categorias?.length !== 8 ||
        d.categorias.some((c,i) => c.id !== categoryIds[i] || typeof c.nombre !== 'string') ||
        d.por_perfil?.length !== data.puntos.length || d.por_cluster?.length !== data.clusters.length) invalid();
    const points = new Map(data.puntos.map(p => [p.usuario_id,p]));
    const seen = new Set(), sums = new Map(data.clusters.map(g => [g.segmento,{total:0,counts:Array(8).fill(0)}]));
    for (const row of d.por_perfil) {
      const p = points.get(row.usuario_id), group = sums.get(row.segmento);
      if (!p || seen.has(row.usuario_id) || p.segmento !== row.segmento || !group ||
          row.total_observaciones !== p.muestras_expresiones_simuladas ||
          !categoryIds.every(id => Number.isInteger(row.conteos?.[id]) && row.conteos[id] >= 0) ||
          categoryIds.reduce((n,id) => n+row.conteos[id],0) !== row.total_observaciones ||
          row.conteos.alegria !== p.expresiones_positivas_conteo_simulado) invalid();
      seen.add(row.usuario_id); group.total += row.total_observaciones;
      categoryIds.forEach((id,i) => group.counts[i] += row.conteos[id]);
    }
    const checkSummary = (row,total,counts) => row && row.total_observaciones === total &&
      categoryIds.every((id,i) => row.conteos?.[id] === counts[i] &&
        Number.isFinite(row.porcentajes?.[id]) && Math.abs(row.porcentajes[id]-(total ? counts[i]*100/total : 0)) < 1e-7);
    const clusterSeen = new Set();
    for (const row of d.por_cluster) {
      const g = sums.get(row.segmento);
      if (!g || clusterSeen.has(row.segmento) || !checkSummary(row,g.total,g.counts)) invalid();
      clusterSeen.add(row.segmento);
    }
    const totals = [...sums.values()];
    if (!checkSummary(d.general,totals.reduce((n,g) => n+g.total,0),
        categoryIds.map((_,i) => totals.reduce((n,g) => n+g.counts[i],0)))) invalid();
  }

  async function renderActive() {
    if (!result) return;
    refreshCounts(); renderGroups();
    $('seg-pca-note').textContent = 'Puntos: perfiles; rombos: centroides. PCA permite ver en 2D un K-Means de cuatro variables y conserva '+
      percent(result.metricas.varianza_pca.reduce((a,b) => a+b,0))+' de la varianza. La leyenda oculta o muestra grupos; los nombres describen esta muestra.';
    $('seg-distribution-note').textContent = 'Cantidad de perfiles en cada grupo; pulsa una barra para filtrarlo. El tamaño de un cluster no implica mejor rendimiento ni una categoría de riesgo.';
    $('seg-comparison-note').textContent = 'Cada punto relaciona asistencia (%) y nota media (0–20) de un perfil sintético. Los colores conservan los grupos del modelo; esta vista no demuestra causalidad.';
    $('seg-expresiones-note').textContent = 'Asistencia y expresiones positivas simuladas, ambas en %. Cada punto es un perfil; las expresiones son sintéticas, no emociones reales ni resultados de EmoScan.';
    const jobs = [scatter('seg-pca','pca_1','pca_2',true),
      scatter('seg-comparison','asistencia_ratio','promedio_notas'),
      scatter('seg-expresiones-scatter','asistencia_ratio','expresiones_positivas_ratio'),
      expressionDistribution(),
      bars('seg-distribution','perfiles','Perfiles',Math.max(...result.clusters.map(p => p.perfiles))*1.2)];
    const ids = ['asistencia','tardanzas','notas','expresiones'];
    for (let i=0;i<features.length;i++) jobs.push(bars('seg-bar-'+ids[i],features[i],labels[i],isRatio(features[i]) ? 100 : 20));
    await Promise.all(jobs);
    // Forzar redimensión para que Plotly calcule dimensiones correctas
    requestAnimationFrame(() => {
      for (const id of chartIds) {
        const el = $(id);
        if (el && window.Plotly && el.data) {
          try { Plotly.Plots.resize(el); } catch(_) {}
        }
      }
    });
  }
  function redraw() {
    const stamp = epoch, ticket = ++renderTicket;
    $('seg-results').setAttribute('aria-busy','true');
    renderQueue = renderQueue.catch(() => {}).then(async () => { if (stamp === epoch && result) await renderActive(); })
      .catch(() => { if (stamp === epoch) error('No se pudo actualizar el gráfico. Restablece la vista o vuelve a procesar el dataset.'); });
    renderQueue = renderQueue.finally(() => { if (ticket === renderTicket) $('seg-results').setAttribute('aria-busy','false'); });
    return renderQueue;
  }
  $('seg-expression-scope').addEventListener('change',() => { if (result) redraw(); });
  $('seg-filter').addEventListener('change',() => { selectedIds.clear(); redraw(); });
  $('seg-reset').addEventListener('click',() => { hiddenGroups.clear(); selectedIds.clear(); $('seg-filter').value = ''; for (const id of chartIds) $(id)._segDragMode = 'zoom'; viewVersion++; redraw(); });
  $('seg-clear-selection').addEventListener('click',() => { selectedIds.clear(); redraw(); });
  function validateResponse(data) {
    if (data.modalidad !== 'principal_4_variables' || data.origen_datos !== 'sintetico' || data.origen_expresiones !== 'sintetico' ||
        data.variables?.length !== 4 || !features.every((f) => data.variables.includes(f)) ||
        !data.puntos?.length || data.puntos.length !== data.metricas?.perfiles || !data.clusters?.length ||
        !Number.isFinite(data.metricas.silueta) || !data.evaluacion_k?.length || typeof data.csv_resultados !== 'string')
      throw new Error('La respuesta del servidor no corresponde a una segmentación sintética de cuatro variables.');
    for (const p of data.puntos) {
      if (!features.every((f) => Number.isFinite(p[f]) && p[f] >= 0 && p[f] <= (isRatio(f) ? 1 : 20)) ||
          !Number.isFinite(p.pca_1) || !Number.isFinite(p.pca_2)) throw new Error('El servidor devolvió variables inválidas. No se mostrarán gráficos.');
    }
  }
  function validateDiagnostics(data) {
    const groups = new Set(data.clusters.map(c => c.segmento));
    if (groups.size !== data.metricas.clusters || data.centroides?.length !== groups.size || data.siluetas?.length !== data.puntos.length)
      throw new Error('La API debe incluir centroides y siluetas por perfil. Reinicia el backend de segmentación y vuelve a intentar.');
    const ids = new Map(data.puntos.map(p => [p.usuario_id,p.segmento]));
    if (new Set(data.centroides.map(c => c.segmento)).size !== groups.size || data.centroides.some(c =>
      !groups.has(c.segmento) || !features.every(f => Number.isFinite(c[f])) || !Number.isFinite(c.pca_1) || !Number.isFinite(c.pca_2) ||
      c.valores_estandarizados?.length !== 4 || !c.valores_estandarizados.every(Number.isFinite)) ||
      new Set(data.siluetas.map(p => p.usuario_id)).size !== ids.size || data.siluetas.some(p =>
      ids.get(p.usuario_id) !== p.segmento || !Number.isFinite(p.silueta) || p.silueta < -1 || p.silueta > 1) ||
      Math.abs(data.siluetas.reduce((n,p) => n+p.silueta,0)/data.siluetas.length-data.metricas.silueta) > 1e-7)
      throw new Error('Los diagnósticos del modelo no son válidos. No se mostrarán gráficos.');
  }
  async function process(mode) {
    if (busy || (mode === 'csv' && !valid)) return;
    const file = $('seg-file').files[0]; if (mode === 'csv' && !file) return;
    busy = true; error(); clearResults(); $('seg-empty').hidden = true;
    $('seg-demo').disabled = true; $('seg-process').disabled = true; $('seg-file').disabled = true;
    $('seg-form').setAttribute('aria-busy','true');
    $('seg-status').textContent = 'Validando datos y calculando StandardScaler, K-Means y PCA…';
    const controller = new AbortController(), timeout = setTimeout(() => controller.abort(),120000);
    try {
      const response = await Panel.api(mode === 'demo' ? '/api/segmentacion/demo' : '/api/segmentacion/procesar',
        mode === 'demo' ? {cache:'no-store',signal:controller.signal} : {method:'POST',
          headers:{'Content-Type':'text/csv','X-CSV-Filename':encodeURIComponent(file.name)},body:file,signal:controller.signal});
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'No se pudo procesar el CSV. Revisa su estructura.');
      validateResponse(data); validateDiagnostics(data); validateExpressionDetail(data);
      result = data; $('seg-expression-scope').value = 'general'; hiddenGroups.clear(); selectedIds.clear(); viewVersion = 0;
      $('seg-filter').replaceChildren(new Option('Todos',''));
      for (const group of data.clusters) $('seg-filter').appendChild(new Option('E'+group.segmento,String(group.segmento)));
      $('seg-count').textContent = fmt(data.metricas.perfiles,0); $('seg-k').textContent = data.metricas.clusters;
      $('seg-score').textContent = fmt(data.metricas.silueta,6); $('seg-variables').textContent = data.variables.length;
      $('seg-dataset').textContent = mode === 'demo' ? 'Demostración de Parte 3' : file.name;
      if (mode === 'csv') $('seg-file-info').textContent = file.name+' · '+fmt(data.metricas.sesiones,0)+' sesiones validadas · '+data.metricas.perfiles+' perfiles';
      $('seg-results').hidden = false; $('seg-upload').open = false;
      $('seg-download').disabled = false; $('seg-filter').disabled = false; await redraw();
      $('seg-status').textContent = 'Análisis listo: '+data.metricas.perfiles+' perfiles sintéticos, '+data.metricas.clusters+' clusters. Explora los gráficos de la cuadrícula.';
    } catch (e) {
      clearResults();
      error(e.name === 'AbortError' ? 'Se superó el tiempo de espera. Prueba con un CSV más pequeño.' :
        e instanceof TypeError ? 'No se pudo conectar con el servidor. Comprueba el backend local y vuelve a intentarlo.' : e.message);
      $('seg-status').textContent = 'No se muestran resultados anteriores. Corrige el archivo o vuelve a intentar la demostración.';
      // panel cerrado
    } finally {
      clearTimeout(timeout); busy = false; $('seg-demo').disabled = false; $('seg-file').disabled = false;
      $('seg-process').disabled = !valid; $('seg-form').setAttribute('aria-busy','false');
    }
  }
  $('seg-open-upload').addEventListener('click', () => {
    $('seg-file').value = '';
    $('seg-file').click();
  });
  $('seg-upload').addEventListener('toggle',() => $('seg-open-upload').setAttribute('aria-expanded',String($('seg-upload').open)));
  $('seg-demo').addEventListener('click',() => process('demo'));
  $('seg-form').addEventListener('submit',(event) => { event.preventDefault(); process('csv'); });
  $('seg-download').addEventListener('click',() => {
    if (!result) return;
    const url = URL.createObjectURL(new Blob(['\uFEFF',result.csv_resultados],{type:'text/csv;charset=utf-8'}));
    const a = document.createElement('a'); a.href = url; a.download = 'segmentacion_sintetica_4_variables.csv';
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url),1000);
  });
  // ── VENTANA FLOTANTE (LIGHTBOX) PARA GRÁFICOS AMPLIADOS ──
  const modalEl = $('seg-chart-modal');
  const modalPlotEl = $('seg-lightbox-plot');
  const modalTitleEl = $('seg-lightbox-title');
  const modalBadgeEl = $('seg-lightbox-badge');
  const modalNoteEl = $('seg-lightbox-note');
  const modalCloseEl = $('seg-lightbox-close');

  async function openChartModal(targetChartId, cardEl) {
    if (!result) return;
    const originalPlot = $(targetChartId);
    let traces = [], layout = {};

    // Obtener título y notas de la tarjeta
    const headingEl = cardEl ? cardEl.querySelector('.seg-chart-heading h3') : null;
    const indexEl = cardEl ? cardEl.querySelector('.seg-chart-index') : null;
    const noteEl = cardEl ? cardEl.querySelector('.seg-chart-note') : null;

    modalTitleEl.textContent = headingEl ? headingEl.textContent.trim() : 'Gráfico ampliado';
    modalBadgeEl.textContent = indexEl ? indexEl.textContent.trim() : '';
    modalBadgeEl.hidden = !modalBadgeEl.textContent;
    modalNoteEl.textContent = noteEl ? noteEl.textContent.trim() : '';

    if (targetChartId === 'seg-means') {
      // Gráfico de 4 variables: construir vista combinada ampliada
      const clusters = result.clusters.map(c => 'E' + c.segmento);
      traces = [
        { name: 'Asistencia (%)', type: 'bar', x: clusters, y: result.clusters.map(c => c.asistencia_ratio * 100), marker: { color: '#f97316' } },
        { name: 'Tardanzas (%)', type: 'bar', x: clusters, y: result.clusters.map(c => c.tardanzas_ratio * 100), marker: { color: '#d97706' } },
        { name: 'Nota media (0-20)', type: 'bar', x: clusters, y: result.clusters.map(c => c.promedio_notas), marker: { color: '#059669' } },
        { name: 'Expresiones sintéticas (%)', type: 'bar', x: clusters, y: result.clusters.map(c => c.expresiones_positivas_ratio * 100), marker: { color: '#9333ea' } }
      ];
      layout = {
        barmode: 'group',
        autosize: true,
        paper_bgcolor: 'transparent',
        plot_bgcolor: '#ffffff',
        font: { family: 'Segoe UI, sans-serif', size: 13, color: '#334e68' },
        margin: { l: 60, r: 25, t: 40, b: 60 },
        legend: { orientation: 'h', x: 0, y: 1.08, font: { size: 12 } },
        xaxis: { title: { text: 'Cluster' }, gridcolor: '#edf1f7' },
        yaxis: { title: { text: 'Valor' }, gridcolor: '#edf1f7' }
      };
    } else if (originalPlot && originalPlot.data && originalPlot.data.length) {
      // Clonar trazas y layout del gráfico original
      traces = JSON.parse(JSON.stringify(originalPlot.data));
      layout = JSON.parse(JSON.stringify(originalPlot.layout || {}));
      layout.autosize = true;
      delete layout.width;
      delete layout.height;
      layout.font = { family: 'Segoe UI, sans-serif', size: 13, color: '#334e68' };
      layout.margin = { l: 65, r: 25, t: 40, b: 65 };
      if (layout.legend) layout.legend.font = { size: 12 };
      if (layout.xaxis && layout.xaxis.title) layout.xaxis.title.font = { size: 13, color: '#173c68' };
      if (layout.yaxis && layout.yaxis.title) layout.yaxis.title.font = { size: 13, color: '#173c68' };
    } else {
      return;
    }

    modalEl.classList.add('open');
    modalEl.setAttribute('aria-hidden', 'false');

    const modalConfig = {
      responsive: true,
      displaylogo: false,
      scrollZoom: true,
      locale: 'es',
      modeBarButtons: [['zoom2d', 'pan2d', 'resetScale2d']]
    };

    await Plotly.newPlot(modalPlotEl, traces, layout, modalConfig);
    setTimeout(() => Plotly.Plots.resize(modalPlotEl), 60);
  }

  function closeChartModal() {
    modalEl.classList.remove('open');
    modalEl.setAttribute('aria-hidden', 'true');
    if (window.Plotly && modalPlotEl.data) {
      Plotly.purge(modalPlotEl);
    }
  }

  if (modalCloseEl) modalCloseEl.addEventListener('click', closeChartModal);
  if (modalEl) {
    modalEl.addEventListener('click', (e) => {
      if (e.target === modalEl) closeChartModal();
    });
  }
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalEl && modalEl.classList.contains('open')) {
      closeChartModal();
    }
  });

  // Delegación de eventos para abrir modal desde las tarjetas o botones de expandir
  document.addEventListener('click', (e) => {
    const expandBtn = e.target.closest('.seg-expand-btn');
    if (expandBtn) {
      e.stopPropagation();
      const chartId = expandBtn.getAttribute('data-target-chart');
      const card = expandBtn.closest('.seg-card');
      openChartModal(chartId, card);
      return;
    }

    const card = e.target.closest('.seg-chart-card, #seg-expression-detail');
    if (card && !e.target.closest('.modebar, .modebar-btn, select, button, a, input, [role="tooltip"]')) {
      const targetPlot = card.querySelector('.seg-plot');
      const chartId = card.getAttribute('data-chart') || (targetPlot ? targetPlot.id : null);
      if (chartId) {
        openChartModal(chartId, card);
      }
    }
  });



  // Autocarga inmediata de la demostración para renderizar todos los gráficos de Plotly al ingresar
  process('demo');
});
