import assert from 'node:assert/strict';
import fs from 'node:fs';
import {compute,normal,dot} from '../visor_piping/model.mjs';
import {pipeFrame,pipeDistance} from '../visor_piping/pipe_path.mjs';
import {splitPipe} from '../visor_piping/split_pipe.mjs';
import {componentCoordinates,annotationPoint} from '../visor_piping/details.mjs';
const catalog=JSON.parse(fs.readFileSync(new URL('../visor_piping/catalogo.json',import.meta.url))),example=JSON.parse(fs.readFileSync(new URL('../visor_piping/ejemplo.json',import.meta.url)));
const near=(a,b)=>assert.ok(Math.hypot(...a.map((x,i)=>x-b[i]))<1e-6,JSON.stringify({a,b}));
const d={...example,equipments:[],components:[{...example.components[0],id:'p',tag:'L-01',parentPort:'origin',nps:6,lengthMM:4000,pipeXMM:200,pipeYMM:-300,pipeZMM:500,pipePitchDeg:20,pipeYawDeg:30,pipeCurveDeg:40,pipeCurveRollDeg:90,outletEnd:'flanged'}]};
let n=compute(d,catalog).nodes[0];near(n.start,[200,-300,500]);assert.ok(n.end[2]>1000);near(pipeFrame(n,0).axis,n.axis);near(pipeFrame(n,n.length).point,n.end);assert.ok(compute(d,catalog).freePorts.some(p=>p.id==='p:in'));
for(const t of [0,.1,.3,.8,1])assert.ok(Math.abs(pipeDistance(n,pipeFrame(n,t*n.length).point)-t*n.length)<1e-6);
const point=pipeFrame(n,3000);d.annotations=[{id:'a',hostType:'component',hostId:'p',coordinates:componentCoordinates(n,point.point),number:'1',text:'Marca',style:'both',color:'#c74336',offsetX:100,offsetY:50}];
d.repairs=[{id:'r',hostId:'p',type:'patch',tag:'REP',comment:'',startMM:2600,lengthMM:300,thicknessMM:4,coverageDeg:90,rollDeg:0}];
d.components.push({...example.components[0],id:'child',tag:'CONT',parentPort:'p:out',lengthMM:500});
d.components.push({...example.components[0],id:'back',tag:'ATRAS',parentPort:'p:in',lengthMM:500});
const before=compute(d,catalog),end=before.nodes.find(n=>n.id==='child').end;
let output=splitPipe(d,'p',1500,catalog,'p2'),after=compute(output.design,catalog);near(after.nodes.find(n=>n.id==='child').end,end);near(annotationPoint(output.design.annotations[0],after,output.design),point.point);assert.equal(output.design.annotations[0].hostId,'p2');assert.equal(output.design.repairs[0].startMM,1100);assert.equal(output.design.repairs[0].hostId,'p2');assert.equal(output.weldTag,'W001');assert.equal(output.design.components.find(c=>c.id==='child').parentPort,'p2:out');assert.equal(output.design.components.find(c=>c.id==='p').outletEnd,'welded');assert.equal(output.design.components.find(c=>c.id==='p2').outletEnd,'flanged');
output=splitPipe(output.design,'p2',500,catalog,'p3');after=compute(output.design,catalog);near(after.nodes.find(n=>n.id==='child').end,end);assert.deepEqual(output.design.components.filter(c=>c.segmentGroup==='p').map(c=>c.tag),['L-01-01','L-01-02','L-01-03']);assert.equal(output.weldTag,'W002');assert.throws(()=>splitPipe(output.design,'p3',700,catalog,'bad'),/reparación/);assert.throws(()=>splitPipe(d,'p',1,catalog,'bad'),/10 mm/);
// Una derivación sigue el eje curvo y cambia de segmento sin desplazarse.
const olet={...example.components[0],kind:'sockolet',id:'so',tag:'SO',parentPort:'p:tap',tapOffsetMM:3200,outNps:2,lengthMM:100};const branched={...d,components:[d.components[0],olet]},bp=compute(branched,catalog).nodes[1].end;const split=splitPipe(branched,'p',1500,catalog,'p2');near(compute(split.design,catalog).nodes.find(n=>n.id==='so').end,bp);
for(const angle of [-120,-.001,0,.001,120]){const x=structuredClone(d);x.components=x.components.slice(0,1);delete x.repairs;delete x.annotations;x.components[0].pipeCurveDeg=angle;const initial=compute(x,catalog);const y=splitPipe(x,'p',1700,catalog,'second');near(compute(y.design,catalog).nodes[1].end,initial.nodes[0].end);}
console.log('Inclinación 3D, arco, soldaduras, puertos, detalles y división repetida: OK');

