/* Browser checks use JSON computed by the actual, unchanged four-variable model. */
module.exports = async function dashboardChecks(teacher,url,fixture,sample,check,small) {
  const p=teacher.page;
  const settled=()=>p.waitForFunction(()=>document.getElementById('seg-results').getAttribute('aria-busy')==='false');
  const ready=async(id)=>{await p.waitForFunction(id=>!!document.getElementById(id).data?.length,id); await settled();};
  const visible=async(count)=>{await p.waitForFunction(count=>document.getElementById('seg-visible').textContent.startsWith(count+' de '),count); await settled();};
  const pause=()=>p.waitForTimeout(150);
  check(await p.locator('.admin-menu').innerText().then(t=>t.includes('Segmentación IA')&&!t.includes('EmoScan')),'Professor menu separated');
  check(await p.locator('[role=tab]').count()===0,'Single page without tabs');
  await p.locator('#seg-demo').click(); await p.locator('#seg-results').waitFor({state:'visible'}); await ready('seg-pca');
  check(await p.locator('#seg-count').innerText()==='150','150 actual demo profiles');
  await require('./segmentacion-categorias.checks.cjs')(teacher,fixture,check);
  check(await p.locator('#seg-k').innerText()==='3','K=3 from API');
  check(await p.locator('#seg-variables').innerText()==='4','All four variables retained');
  check(await p.locator('#seg-score').innerText()===fixture.metricas.silueta.toLocaleString('es-PE',{maximumFractionDigits:6}),'Silueta displayed to six decimals');
  check(await p.locator('.seg-chart-grid > article:visible').count()===8,'Eight analysis cards visible together');
  check(await p.locator('#seg-tardanzas-scatter').count()===0,'Tardiness dispersion remains excluded');
  check(await p.evaluate(()=>document.getElementById('seg-pca').data.filter(t=>!t.meta.centroide).reduce((n,t)=>n+t.x.length,0))===150,'PCA retains all 150 profiles');
  check(await p.evaluate(()=>document.getElementById('seg-pca').data.filter(t=>t.meta.centroide).map(t=>[t.x[0],t.y[0]])).then(c=>JSON.stringify(c)===JSON.stringify(fixture.centroides.map(c=>[c.pca_1,c.pca_2]))),'Actual projected centroid positions');
  check(await p.evaluate(()=>document.getElementById('seg-pca').data.filter(t=>t.meta.centroide).every(t=>t.marker.symbol==='diamond')),'Centroids differ from profiles');
  check(await p.locator('#seg-groups').innerText().then(t=>['Asistencia baja','Asistencia intermedia','Asistencia relativamente alta','35,60','71,48','76,05','11,10','14,65','15,38'].every(s=>t.includes(s))),'Descriptive groups match actual demo means');
  check(await p.evaluate(()=>document.getElementById('seg-distribution').data.map(t=>t.y[0])).then(v=>v.join(',')==='45,60,45'),'Population bars match real demo');
  check(await p.evaluate(()=>document.getElementById('seg-samples').data.flatMap(t=>t.x).sort((a,b)=>a-b)).then(v=>JSON.stringify(v)===JSON.stringify(fixture.siluetas.map(p=>p.silueta).sort((a,b)=>a-b))),'All individual silhouette values come from API');
  check(await p.evaluate(()=>document.getElementById('seg-samples').layout.shapes[0].x0)===fixture.metricas.silueta,'Silhouette mean reference');
  check(await p.evaluate(()=>document.getElementById('seg-heatmap').data[0].z).then(z=>JSON.stringify(z)===JSON.stringify(fixture.centroides.map(c=>c.valores_estandarizados))),'Heatmap uses actual standardized centroids');
  check(await p.evaluate(()=>document.getElementById('seg-heatmap').data[0].type)==='heatmap','Real Plotly heatmap is registered');
  check(await p.evaluate(()=>document.getElementById('seg-elbow').data[0].y).then(v=>v.join(',')===fixture.evaluacion_k.map(p=>p.inercia).join(',')),'Elbow uses actual inertia values');
  check(await p.evaluate(()=>document.getElementById('seg-elbow').layout.shapes[0].x0)===3,'Chosen K marker');
  check(await p.locator('#seg-choice-note').innerText().then(t=>t.includes('K global: 2')&&t.includes('K=4')&&t.includes('no es un porcentaje de precisión')),'Documented K selection and precision caveat');
  const dispersions=['seg-pca','seg-comparison','seg-expresiones-scatter'];
  for(const id of dispersions) {
    check(await p.evaluate(id=>document.getElementById(id).data.filter(t=>!t.meta.centroide).reduce((n,t)=>n+t.x.length,0),id)===150,'All 150 profiles in '+id);
    check(await p.evaluate(id=>document.getElementById(id).data.filter(t=>!t.meta.centroide).map(t=>t.marker.color),id).then(v=>v.join(',')==='#2563eb,#d97706,#059669'),'Consistent cluster colors in '+id);
  }
  check(await p.evaluate(()=>document.getElementById('seg-comparison')._fullLayout.xaxis.range[1]===100&&document.getElementById('seg-comparison')._fullLayout.yaxis.range[1]===20),'Attendance vs grades uses correct scales');
  check(await p.evaluate(()=>document.getElementById('seg-expresiones-scatter')._fullLayout.xaxis.range[1]===100&&document.getElementById('seg-expresiones-scatter')._fullLayout.yaxis.range[1]===100),'Synthetic expression comparison uses percentage scales');
  check(await p.evaluate(()=>document.getElementById('seg-comparison').data[0].y[0])===fixture.puntos.find(p=>p.segmento===1).promedio_notas,'Grades dispersion uses actual values');
  check(await p.evaluate(()=>document.getElementById('seg-expresiones-scatter').data[0].y[0])===fixture.puntos.find(p=>p.segmento===1).expresiones_positivas_ratio*100,'Expression dispersion uses actual values');
  check(await p.evaluate(()=>document.getElementById('seg-bar-notas')._fullLayout.yaxis.range[1])===20,'Grades retain 0-20 scale');
  check(await p.evaluate(()=>document.getElementById('seg-bar-asistencia')._fullLayout.yaxis.range[1])===100,'Percentages retain 0-100 scale');
  await p.locator('#seg-filter').selectOption('1'); await visible(45);
  check(await p.locator('#seg-groups .seg-group').count()===1,'Global filter updates group summary');
  check(await p.evaluate(ids=>ids.every(id=>document.getElementById(id).data.filter(t=>!t.meta.centroide&&t.visible===true).length===1),dispersions),'Global filter applies to all three dispersions');

  check(await p.evaluate(()=>document.getElementById('seg-heatmap').data[0].z.length)===1,'Filter applies to heatmap');
  check(await p.evaluate(()=>document.getElementById('seg-samples').data.filter(t=>t.visible===true).length)===1,'Filter applies to silhouette bars');
  await p.locator('#seg-reset').click(); await visible(150);
  await p.locator('#seg-comparison .scatterlayer .point').first().click({force:true}); await settled();
  check(await p.evaluate(ids=>ids.every(id=>document.getElementById(id).data.filter(t=>!t.meta.centroide).reduce((n,t)=>n+(t.selectedpoints?.length||0),0)===1),dispersions),'Selecting a complementary profile synchronizes all three dispersions');
  await p.locator('#seg-clear-selection').click(); await settled();
  await p.locator('#seg-pca .scatterlayer .point').first().hover({force:true});
  await p.waitForFunction(()=>document.querySelector('#seg-pca-tooltip')?.textContent.includes('Expresiones sintéticas'));
  const tooltip=await p.locator('#seg-pca-tooltip').textContent();
  check(['Perfil','Asistencia','Tardanzas','Nota media','Expresiones sintéticas'].every(t=>tooltip.includes(t)),'Actual hover shows cluster and four variables');
  await p.locator('#seg-pca .scatterlayer .point').first().click({force:true});
  await p.waitForFunction(()=>!document.getElementById('seg-selection').hidden);
  check(await p.locator('#seg-selection-body tr').count()===1,'Point click selects a profile');
  await p.locator('#seg-clear-selection').click();
  await p.waitForFunction(()=>document.getElementById('seg-selection').hidden);
  await settled(); await p.locator('#seg-pca').scrollIntoViewIfNeeded();
  let box=await p.locator('#seg-pca .nsewdrag').boundingBox();
  await p.locator('#seg-pca').hover(); await p.locator('#seg-pca .modebar-btn').nth(2).click();
  await p.mouse.move(box.x+12,box.y+12); await p.mouse.down();
  await p.mouse.move(box.x+box.width*.55,box.y+box.height-2,{steps:15}); await p.mouse.up();
  await p.waitForFunction(()=>!document.getElementById('seg-selection').hidden);
  check(await p.locator('#seg-selection-count').innerText().then(t=>parseInt(t)>1),'Box selection selects multiple actual points');
  await p.locator('#seg-clear-selection').click(); await pause();
  await settled(); await p.locator('#seg-pca').scrollIntoViewIfNeeded(); box=await p.locator('#seg-pca .nsewdrag').boundingBox();
  const original=await p.evaluate(()=>document.getElementById('seg-pca')._fullLayout.xaxis.range.slice());
  await p.locator('#seg-pca').hover(); await p.locator('#seg-pca .modebar-btn').nth(0).click();
  await p.mouse.move(box.x+box.width*.2,box.y+box.height*.2); await p.mouse.down();
  await p.mouse.move(box.x+box.width*.8,box.y+box.height*.8,{steps:15}); await p.mouse.up();
  await p.waitForFunction((range)=>document.getElementById('seg-pca')._fullLayout.xaxis.range[0]!==range[0],original);
  check(true,'Mouse drag zoom changes the actual plot range');
  const zoomed=await p.evaluate(()=>document.getElementById('seg-pca')._fullLayout.xaxis.range.slice());
  await p.locator('#seg-pca').hover(); await p.locator('#seg-pca .modebar-btn').nth(1).click();
  await p.mouse.move(box.x+box.width*.5,box.y+box.height*.5); await p.mouse.down();
  await p.mouse.move(box.x+box.width*.65,box.y+box.height*.5,{steps:10}); await p.mouse.up();
  await p.waitForFunction((range)=>document.getElementById('seg-pca')._fullLayout.xaxis.range[0]!==range[0],zoomed);
  check(true,'Mouse drag pan changes the actual plot range');
  await p.locator('#seg-pca').hover(); await p.locator('#seg-pca .modebar-btn').nth(3).click();
  await p.waitForFunction((range)=>Math.abs(document.getElementById('seg-pca')._fullLayout.xaxis.range[0]-range[0])<1e-8,original);
  check(true,'Toolbar reset restores the original PCA range');

  await p.locator('#seg-reset').click();
  await p.waitForFunction((range)=>Math.abs(document.getElementById('seg-pca')._fullLayout.xaxis.range[0]-range[0])<1e-8,original);
  check(true,'Reset restores the initial PCA view');
  await p.locator('#seg-pca .legend .legendtoggle').first().click(); await visible(105);
  check(await p.evaluate(()=>document.getElementById('seg-pca').data[0].visible)==='legendonly','Legend hides E1 and updates global visible count');
  await p.locator('#seg-pca .legend .legendtoggle').first().click(); await visible(150);
  await p.locator('#seg-filter').selectOption('2'); await visible(60);
  await p.locator('#seg-reset').click(); await visible(150);
  for(let i=0;i<fixture.clusters.length;i++) {
    await p.locator('#seg-pca .legend .legendtoggle').nth(i).click(); await settled();
  }
  await visible(0);
  check(await p.evaluate(()=>document.getElementById('seg-heatmap').data[0].z.length)===0,'Empty global filter produces an empty heatmap');
  check(await p.locator('#seg-error').isHidden(),'Hiding all clusters has no rendering error');
  await p.locator('#seg-reset').click(); await visible(150);
  // Reverse labels while preserving every underlying point and measurement.
  // This proves descriptive names follow the means, not an E1/E3 assumption.
  const renamed=JSON.parse(JSON.stringify(fixture));
  for(const key of ['puntos','clusters','centroides','siluetas']) for(const row of renamed[key]) row.segmento=4-row.segmento;
  renamed.clusters.sort((a,b)=>a.segmento-b.segmento);
  renamed.centroides.sort((a,b)=>a.segmento-b.segmento);
  for(const row of renamed.expresiones_categoricas.por_perfil) row.segmento=4-row.segmento;
  for(const row of renamed.expresiones_categoricas.por_cluster) row.segmento=4-row.segmento;
  renamed.expresiones_categoricas.por_cluster.sort((a,b)=>a.segmento-b.segmento);

  teacher.state.override=renamed;
  await p.locator('#seg-demo').click(); await ready('seg-pca');
  check(await p.locator('#seg-groups .seg-group').first().innerText().then(t=>t.includes('E1 — Asistencia relativamente alta')),'Description follows observed means when cluster ids change');
  teacher.state.override=null;
  await p.locator('#seg-demo').click(); await ready('seg-pca');
  const order=['seg-pca','seg-samples','seg-comparison','seg-expresiones-scatter','seg-elbow','seg-heatmap','seg-distribution','seg-means'];
  check(await p.locator('.seg-chart-grid > article').evaluateAll(nodes=>nodes.map(n=>n.dataset.chart)).then(v=>v.join(',')===order.join(',')),'Educational grid order');
  for(const [width,height] of [[1366,768],[1920,1080],[390,844]]){
    await p.setViewportSize({width,height}); await p.waitForTimeout(400);
    await p.waitForFunction(()=>[...document.querySelectorAll('.seg-plot')].every(gd=>Math.abs(gd._fullLayout.width-gd.clientWidth)<3));
    check(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2),'No horizontal overflow at '+width);
    check(await p.evaluate(width=>{
      const c=[...document.querySelectorAll('.seg-chart-grid > article')].map(n=>n.getBoundingClientRect());
      return width>650 ? Math.abs(c[0].top-c[1].top)<2&&Math.abs(c[0].height-c[1].height)<2&&c[0].width>c[1].width&&Math.abs(c[2].top-c[3].top)<2&&Math.abs(c[4].top-c[5].top)<2&&Math.abs(c[6].top-c[7].top)<2 : c[1].top>=c[0].bottom;
    },width),'Responsive columns and consistent row heights at '+width);
    check(await p.evaluate(()=>[...document.querySelectorAll('.seg-plot')].every(gd=>gd._fullLayout.width<=gd.parentElement.clientWidth&&gd._fullLayout._size.w>60&&gd._fullLayout._size.h>50)),'All plots resize at '+width);
    check(await p.evaluate(()=>[...document.querySelectorAll('h1,h3,h4,.seg-group button,.seg-chart-note')].every(n=>n.scrollWidth<=n.clientWidth+1)),'Texts fit at '+width);
    await require('./segmentacion-tooltips.checks.cjs')(p,fixture,check,width);
    await require('./segmentacion-categorias.checks.cjs').viewport(p,fixture,check,width);
    if(process.env.QA_ARTIFACTS) {
      await p.mouse.move(0,0); await p.evaluate(()=>scrollTo(0,0));
      await p.screenshot({path:require('node:path').join(process.env.QA_ARTIFACTS,'dashboard-'+width+'.png'),fullPage:true});
    }
  }
  await p.setViewportSize({width:1366,height:768}); await pause();
  const downloading=p.waitForEvent('download'); await p.locator('#seg-download').click(); const download=await downloading;
  const stream=await download.createReadStream(),chunks=[]; for await(const chunk of stream) chunks.push(chunk);
  check(Buffer.concat(chunks).toString('utf8').replace(/^\uFEFF/,'')===fixture.csv_resultados,'Download is complete actual result CSV');
  await p.locator('#seg-open-upload').click();
  await p.locator('#seg-file').setInputFiles({name:'incorrecto.csv',mimeType:'text/csv',buffer:Buffer.from('usuario_id,estado\n1,PRESENTE')});
  await p.locator('#seg-error').waitFor({state:'visible'});
  check(await p.locator('#seg-error').innerText().then(t=>t.includes('Faltan columnas')),'Missing columns explained');
  check(await p.locator('#seg-results').isHidden(),'Invalid new file clears previous analysis');
  check(await p.evaluate(()=>!document.getElementById('seg-pca').data&&document.getElementById('seg-count').textContent==='—'),'No old Plotly points or metric cards retained');
  await p.locator('#seg-file').setInputFiles({name:'grande.csv',mimeType:'text/csv',buffer:Buffer.alloc(2*1024*1024+1)});
  await p.waitForFunction(()=>document.getElementById('seg-error').textContent.includes('2 MiB'));
  check(await p.locator('#seg-process').isDisabled(),'Large file cannot be submitted');
  await p.locator('#seg-file').setInputFiles({name:'real.csv',mimeType:'text/csv',buffer:Buffer.from(sample.toString().replaceAll(',sintetico',',real'))});
  await p.waitForFunction(()=>!document.getElementById('seg-process').disabled); await p.locator('#seg-process').click();
  await p.waitForFunction(()=>document.getElementById('seg-error').textContent.includes('origen_datos=sintetico'));
  check(await p.locator('#seg-results').isHidden(),'Server rejection does not retain old results');
  await p.locator('#seg-drop').evaluate((element,text)=>{
    const transfer=new DataTransfer(); transfer.items.add(new File([text],'sintetico.csv',{type:'text/csv'}));
    element.dispatchEvent(new DragEvent('drop',{dataTransfer:transfer,bubbles:true,cancelable:true}));
  },sample.toString());
  await p.waitForFunction(()=>!document.getElementById('seg-process').disabled); await p.locator('#seg-process').click();
  await p.locator('#seg-results').waitFor({state:'visible'}); await ready('seg-distribution');
  check(await p.locator('#seg-count').innerText()==='150','Drag-and-drop CSV renders newly processed data');
  check(await p.locator('#seg-file-info').textContent().then(t=>t.includes('sesiones validadas')),'Row count uses validated server metadata');
  check(await p.locator('#seg-expression-detail').isHidden(),'Legacy CSV still works and hides categorical detail');
  check(await p.evaluate(()=>!document.getElementById('seg-expression-chart').data),'Legacy CSV purges previous categorical observations');

  await p.locator('#seg-filter').selectOption('1');
  await p.locator('#seg-open-upload').click();
  const lines=sample.toString().trimEnd().split(/\r?\n/),smaller=lines.filter((line,i)=>i===0||Number(line.split(',')[0])<=20).join('\n')+'\n';
  await p.locator('#seg-file').setInputFiles({name:'pequeno.csv',mimeType:'text/csv',buffer:Buffer.from(smaller)});
  await p.waitForFunction(()=>!document.getElementById('seg-process').disabled); await p.locator('#seg-process').click();
  await p.waitForFunction(()=>document.getElementById('seg-count').textContent==='20'); await ready('seg-distribution');
  check(await p.locator('#seg-k').innerText()===String(small.metricas.clusters),'New file updates computed K');
  check(await p.locator('#seg-filter').inputValue()===''&&await p.locator('#seg-filter option').count()===small.clusters.length+1,'New file resets filters and rebuilds cluster choices');
  await ready('seg-pca');
  check(await p.evaluate(()=>document.getElementById('seg-pca').data.filter(t=>!t.meta.centroide).reduce((n,t)=>n+t.x.length,0))===20,'New CSV replaces all previous PCA points');
  check(await p.locator('#seg-selection').isHidden(),'New dataset clears previous selection');
  check(await p.locator('#seg-expression-detail').isHidden(),'20-profile legacy dataset does not invent category detail');
  for(const id of dispersions) {
    const xy=id==='seg-pca' ? ['pca_1','pca_2'] : ['asistencia_ratio',id==='seg-comparison'?'promedio_notas':'expresiones_positivas_ratio'];
    check(await p.evaluate(id=>document.getElementById(id).data.filter(t=>!t.meta.centroide).map(t=>[t.x,t.y]),id).then(actual=>{
      const expected=small.clusters.map(c=>{
        const points=small.puntos.filter(p=>p.segmento===c.segmento);
        return xy.map(f=>points.map(p=>p[f]*(f.endsWith('_ratio')?100:1)));
      });
      return JSON.stringify(actual)===JSON.stringify(expected);
    }),'New CSV replaces all coordinates in '+id);
  }
  check(await p.evaluate(()=>document.getElementById('seg-elbow').data[0].y).then(v=>JSON.stringify(v)===JSON.stringify(small.evaluacion_k.map(r=>r.inercia))),'New CSV replaces the elbow curve');
  check(await p.evaluate(()=>document.getElementById('seg-distribution').data.map(t=>t.y[0])).then(v=>JSON.stringify(v)===JSON.stringify(small.clusters.map(r=>r.perfiles))),'New CSV replaces distribution counts');
  check(await p.evaluate(()=>['asistencia','tardanzas','notas','expresiones'].map(id=>document.getElementById('seg-bar-'+id).data.map(t=>t.y[0]))).then(v=>{
    const fields=['asistencia_ratio','tardanzas_ratio','promedio_notas','expresiones_positivas_ratio'];
    return JSON.stringify(v)===JSON.stringify(fields.map(f=>small.clusters.map(c=>c[f]*(f.endsWith('_ratio')?100:1))));
  }),'New CSV replaces means of all four variables');

  check(await p.evaluate(()=>document.getElementById('seg-samples').data.reduce((n,t)=>n+t.x.length,0))===20,'New CSV replaces individual silhouettes');
  check(await p.evaluate(()=>document.getElementById('seg-heatmap').data[0].z.length)===small.clusters.length,'New CSV rebuilds heatmap');
  check(await p.evaluate(()=>document.getElementById('seg-pca').data.filter(t=>t.meta.centroide).map(t=>[t.x[0],t.y[0]])) .then(coords=>JSON.stringify(coords)===JSON.stringify(small.centroides.map(c=>[c.pca_1,c.pca_2]))),'New CSV replaces projected centroids');

  teacher.state.override={...fixture,centroides:[]};
  await p.locator('#seg-demo').click();
  await p.waitForFunction(()=>document.getElementById('seg-error').textContent.includes('API debe incluir'));
  check(await p.locator('#seg-results').isHidden(),'Incomplete diagnostic payload is rejected without old charts');
  teacher.state.override=null;
  teacher.state.badResponse=true;
  await p.locator('#seg-demo').click();
  await p.waitForFunction(()=>document.getElementById('seg-error').textContent.includes('variables inválidas'));
  check(await p.locator('#seg-results').isHidden(),'Malformed four-variable response is rejected without stale data');
  teacher.state.badResponse=false;
  await p.locator('#seg-demo').click(); await p.locator('#seg-results').waitFor({state:'visible'}); await ready('seg-distribution');
  check(await p.locator('#seg-count').innerText()==='150','Can recover to actual demo after rejected response');
  await p.locator('#seg-open-upload').click();
  await p.locator('#seg-file').setInputFiles({name:'parcial.csv',mimeType:'text/csv',buffer:Buffer.from('usuario_id,sesion,estado,promedio_notas,origen_datos,exp_sint_neutral\n1,1,PRESENTE,15,sintetico,2')});
  await p.waitForFunction(()=>document.getElementById('seg-error').textContent.includes('Detalle categórico incompleto'));
  check(await p.locator('#seg-process').isDisabled(),'Incomplete optional CSV schema is explained before submission');
  const rich=require('node:fs').readFileSync(require('node:path').resolve(__dirname,'../ejemplos/segmentacion_sintetica_categorias.csv'));
  await p.locator('#seg-file').setInputFiles({name:'categorias.csv',mimeType:'text/csv',buffer:rich});
  await p.waitForFunction(()=>!document.getElementById('seg-process').disabled);
  await p.locator('#seg-process').click();
  await ready('seg-expression-chart');
  check(await p.locator('#seg-expression-detail').isVisible(),'Valid optional categories render after upload');
  check(await p.evaluate(()=>document.getElementById('seg-expression-chart').data[0].x.reduce((a,b)=>a+b,0))===6000,'Uploaded categorical dataset displays 6000 observations');

};
