/* Detailed observations are synthetic counts, never proportions of real students. */
module.exports=async function categoryChecks(teacher,fixture,check) {
  const p=teacher.page,d=fixture.expresiones_categoricas;
  const settled=()=>p.waitForFunction(()=>document.getElementById('seg-results').getAttribute('aria-busy')==='false');
  check(await p.locator('#seg-expression-detail').isVisible(),'Detail appears for sufficient synthetic observations');
  check(await p.evaluate(()=>document.getElementById('seg-expression-chart').data[0].x).then(v=>JSON.stringify(v)===JSON.stringify(d.categorias.map(c=>d.general.conteos[c.id]))),'General chart equals all synthetic observation counts');
  check(await p.evaluate(()=>document.getElementById('seg-expression-chart').data[0].customdata).then(v=>v.every((row,i)=>row[1]===6000&&Math.abs(row[0]-d.general.porcentajes[d.categorias[i].id])<1e-9)),'General percentages divide by 6000 observations, not 150 profiles');
  check(await p.locator('#seg-expression-note').innerText().then(t=>t.includes('no reconstrucción')&&t.includes('no porcentajes de estudiantes')),'New synthetic convention is explicit');
  await p.locator('#seg-expression-scope').selectOption('cluster');await settled();
  check(await p.evaluate(()=>document.getElementById('seg-expression-chart').data.length)===8,'Eight category traces by cluster');
  check(await p.evaluate(()=>Math.abs(document.getElementById('seg-expression-chart')._fullLayout.yaxis.range[1]-2688)<1e-8),'Changing chart orientation resets the count axis');
  check(await p.evaluate(()=>document.getElementById('seg-expression-chart').data.map(t=>t.y)).then(v=>v.every((row,i)=>row.every((n,j)=>n===d.por_cluster[j].conteos[d.categorias[i].id]))),'Category distributions match backend cluster aggregates');
  await p.locator('#seg-filter').selectOption('1');await settled();
  check(await p.evaluate(()=>document.getElementById('seg-expression-chart').data.every(t=>t.x.length===1)),'Global cluster filter applies to detailed observations');
  check(await p.evaluate(()=>document.getElementById('seg-expression-chart').data.every(t=>t.customdata[0][1]===1800)),'Cluster percentages use 1800 observations of E1');
  await p.locator('#seg-reset').click();await settled();
  await p.locator('#seg-expression-scope').selectOption('general');await settled();
  teacher.state.override=JSON.parse(JSON.stringify(fixture));
  teacher.state.override.expresiones_categoricas.por_perfil[0].conteos.neutral++;
  await p.locator('#seg-demo').click();
  await p.waitForFunction(()=>document.getElementById('seg-error').textContent.includes('detalle de expresiones sintéticas'));
  check(await p.locator('#seg-results').isHidden(),'Inconsistent detailed payload clears old results');
  teacher.state.override=null;await p.locator('#seg-demo').click();
  await p.waitForFunction(()=>!!document.getElementById('seg-expression-chart').data);await settled();
};

// Both detailed views are exercised at every viewport with real pointer hovers.
module.exports.viewport=async function(p,fixture,check,width) {
  const settled=()=>p.waitForFunction(()=>document.getElementById('seg-results').getAttribute('aria-busy')==='false');
  for(const mode of ['general','cluster']) {
    await p.locator('#seg-expression-scope').selectOption(mode);await settled();
    await p.locator('#seg-expression-chart').scrollIntoViewIfNeeded();
    const bars=p.locator('#seg-expression-chart .barlayer .point path');
    const largest=await bars.evaluateAll(nodes=>nodes.map((n,i)=>({i,a:n.getBoundingClientRect().width*n.getBoundingClientRect().height})).sort((a,b)=>b.a-a.a)[0].i);
    await bars.nth(largest).hover({force:true});
    await p.waitForFunction(()=>document.querySelector('#seg-expression-chart .hoverlayer')?.textContent.includes('observaciones simuladas'));
    check(await p.locator('#seg-expression-chart .hoverlayer').textContent().then(t=>t.includes('%')&&t.includes('observaciones')),'Real quantity and observation percentage hover in '+mode+' at '+width);
    check(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2),'Category '+mode+' fits width '+width);
    check(await p.evaluate(()=>{const gd=document.getElementById('seg-expression-chart');return gd._fullLayout.width<=gd.clientWidth+1&&gd._fullLayout._size.w>150&&gd._fullLayout._size.h>100;}),'Category '+mode+' plot resizes at '+width);
    if(process.env.QA_ARTIFACTS) {
      await p.mouse.move(0,0);await p.waitForTimeout(350);
      await p.locator('#seg-expression-detail').screenshot({path:require('node:path').join(process.env.QA_ARTIFACTS,'categorias-'+mode+'-'+width+'.png')});
    }
  }
  await p.locator('#seg-expression-scope').selectOption('general');await settled();
};
