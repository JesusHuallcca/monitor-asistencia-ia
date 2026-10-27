/* Real Chrome pointer hovers: verify tooltip values and containment at plot extremes. */
module.exports = async function tooltipChecks(p,fixture,check,width) {
  const ids=['seg-pca','seg-comparison','seg-expresiones-scatter'];
  const num=(v,d)=>Number(v).toLocaleString('es-ES',{minimumFractionDigits:d,maximumFractionDigits:d});
  for(const id of ids) {
    await p.locator('#'+id).scrollIntoViewIfNeeded();
    const tip=p.locator('#'+id+'-tooltip');
    const indices=await p.locator('#'+id+' .scatterlayer .point').evaluateAll(nodes=>{
      const points=nodes.map((node,i)=>{const b=node.getBoundingClientRect();return {i,x:b.x+b.width/2,y:b.y+b.height/2};});
      return [points.reduce((a,b)=>a.x<b.x?a:b).i,points.reduce((a,b)=>a.x>b.x?a:b).i,
        points.reduce((a,b)=>a.y<b.y?a:b).i,points.reduce((a,b)=>a.y>b.y?a:b).i];
    });
    const seen=new Set();
    for(const index of indices) {
      await p.locator('#'+id).locator('..').scrollIntoViewIfNeeded();
      await p.locator('#'+id+' .scatterlayer .point').nth(index).hover({force:true});
      await tip.waitFor({state:'visible'});
      const text=await tip.innerText(), match=text.match(/Perfil (.+) · Grupo E(\d+)/);
      const point=fixture.puntos.find(p=>String(p.usuario_id)===match?.[1]);
      check(!!point&&String(point.segmento)===match[2]&&
        text.includes('Asistencia: '+num(point.asistencia_ratio*100,1)+' %')&&
        text.includes('Tardanzas: '+num(point.tardanzas_ratio*100,1)+' %')&&
        text.includes('Nota media: '+num(point.promedio_notas,2))&&
        text.includes('Expresiones sintéticas: '+num(point.expresiones_positivas_ratio*100,1)+' %'),
        'Dynamic tooltip values at '+id+' edge, width '+width);
      seen.add(match[1]);
      check(await tip.evaluate(el=>{
        const t=el.getBoundingClientRect(),card=el.closest('article').getBoundingClientRect();
        const plot=el.closest('article').querySelector('.nsewdrag').getBoundingClientRect();
        const style=getComputedStyle(el);
        return t.left>=card.left&&t.right<=card.right&&t.top>=plot.bottom&&t.bottom<=card.bottom&&
          t.width<=250&&t.height<=112&&style.backgroundColor==='rgb(255, 255, 255)'&&
          parseFloat(style.borderRadius)>=8&&el.scrollWidth<=el.clientWidth;
      }),'Compact white tooltip stays below drawing and inside card at '+id+', width '+width);
    }
    check(seen.size>1,'Tooltip follows different profiles at '+id+', width '+width);
    check(await p.locator('#'+id+' .hoverlayer .hovertext').count()===0,'No native cluster-colored balloon at '+id);
    await p.mouse.move(0,0); await p.waitForTimeout(350);
    check(await tip.isHidden(),'Tooltip clears on leaving '+id);
    check(await p.locator('#'+id+' .modebar-group').first().evaluate(el=>Number(getComputedStyle(el).opacity)===0),'Tools hidden away from '+id);
    await p.locator('#'+id).hover(); await p.waitForTimeout(350);
    check(await p.locator('#'+id+' .modebar-group').first().evaluate(el=>Number(getComputedStyle(el).opacity)===1),'Tools appear on hover at '+id);
    check(await p.locator('#'+id+' .modebar-btn').count()===4,'Only zoom, pan, select and reset at '+id);
    if(id!=='seg-pca') {
      await p.locator('#'+id).scrollIntoViewIfNeeded();
      const before=await p.evaluate(id=>document.getElementById(id)._fullLayout.xaxis.range.slice(),id);
      await p.locator('#'+id).hover(); await p.locator('#'+id+' .modebar-btn').nth(0).click();
      const box=await p.locator('#'+id+' .nsewdrag').boundingBox();
      await p.mouse.move(box.x+box.width*.2,box.y+box.height*.2); await p.mouse.down();
      await p.mouse.move(box.x+box.width*.8,box.y+box.height*.8,{steps:12}); await p.mouse.up();
      await p.waitForFunction(({id,before})=>document.getElementById(id)._fullLayout.xaxis.range[0]!==before[0],{id,before});
      check(true,'Actual zoom gesture in '+id+' at '+width);
      await p.locator('#'+id).hover(); await p.locator('#'+id+' .modebar-btn').nth(3).click();
      await p.waitForFunction(({id,before})=>document.getElementById(id)._fullLayout.xaxis.range.every((v,i)=>Math.abs(v-before[i])<1e-8),{id,before});
      check(true,'Toolbar reset restores '+id+' at '+width);
    }
    if(process.env.QA_ARTIFACTS&&id==='seg-pca') {
      await p.locator('#'+id).locator('..').scrollIntoViewIfNeeded();
      await p.locator('#'+id+' .scatterlayer .point').nth(indices[1]).hover({force:true});
      await tip.waitFor({state:'visible'});
      await p.locator('#'+id).locator('..').screenshot({path:require('node:path').join(process.env.QA_ARTIFACTS,'tooltip-pca-'+width+'.png')});
    }
  }
  await p.locator('#seg-pca').scrollIntoViewIfNeeded();
  await p.locator('#seg-pca .scatterlayer .trace').nth(fixture.clusters.length).locator('.point').hover({force:true});
  await p.locator('#seg-pca-tooltip').waitFor({state:'visible'});
  check(await p.locator('#seg-pca-tooltip').innerText().then(t=>t.startsWith('Centroide · Grupo E')),'Centroid hover is distinguished from a student profile');
  await p.locator('#seg-samples').scrollIntoViewIfNeeded();
  const bars=p.locator('#seg-samples .barlayer .point path');
  const widest=await bars.evaluateAll(nodes=>nodes.map((n,i)=>({i,w:n.getBoundingClientRect().width})).sort((a,b)=>b.w-a.w)[0].i);
  await bars.nth(widest).hover({force:true});
  await p.locator('#seg-samples-tooltip').waitFor({state:'visible'});
  check(await p.locator('#seg-samples-tooltip').innerText().then(t=>t.includes('Silueta:')&&t.includes('Perfil')),'Individual silhouette has dynamic profile and coefficient tooltip');
  await p.locator('#seg-heatmap').scrollIntoViewIfNeeded();
  const box=await p.locator('#seg-heatmap .nsewdrag').boundingBox();
  await p.mouse.move(box.x+box.width/8,box.y+box.height/(2*fixture.clusters.length));
  await p.waitForFunction(()=>document.querySelector('#seg-heatmap .hoverlayer')?.textContent.includes('Centroide estandarizado'));
  check(await p.locator('#seg-heatmap .hoverlayer').textContent().then(t=>t.includes('Asistencia')),'Real heatmap cell hover shows variable and standardized centroid');

};
