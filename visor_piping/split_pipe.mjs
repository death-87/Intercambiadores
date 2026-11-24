import {compute,normal,dot,cross} from './model.mjs';
import {pipeFrame} from './pipe_path.mjs';
import {annotationPoint,componentCoordinates} from './details.mjs';
import {sortComponents} from './equipment.mjs';
// Transacción pura: conserva la geometría, los puertos y los detalles del proyecto.
export function splitPipe(design,id,distance,catalog,newId){
 const d=structuredClone(design),before=compute(d,catalog),node=before.nodes.find(n=>n.id===id),c=d.components.find(n=>n.id===id);
 if(!node||c.kind!=='pipe')throw Error('Elige un punto sobre un tramo de tubo.');
 if(!Number.isFinite(distance)||distance<10||c.lengthMM-distance<10)throw Error('Deja al menos 10 mm a cada extremo de la soldadura.');
 if(d.components.length>=200||d.components.some(c=>c.id===newId))throw Error('No es posible agregar otro segmento.');
 if((d.repairs||[]).some(r=>r.hostId===id&&r.startMM<distance&&r.startMM+r.lengthMM>distance))throw Error('La soldadura cruza una reparación. Elige un punto fuera del refuerzo o parche.');
 const points=new Map((d.annotations||[]).filter(a=>a.hostType==='component'&&a.hostId===id).map(a=>[a.id,annotationPoint(a,before,d)]));
 const oldLength=c.lengthMM,base=(c.segmentBase||c.tag).slice(0,30),group=c.segmentGroup||id,frame=pipeFrame(node,distance),u=normal(frame.axis),b=cross(frame.axis,u),roll=Math.atan2(dot(frame.normal,b),dot(frame.normal,u))*180/Math.PI;
 let number=1;while(d.components.some(c=>c.weldTag==='W'+String(number).padStart(3,'0')))number++;
 const second={...c,id:newId,parentPort:id+':out',lengthMM:oldLength-distance,inletEnd:'welded',pipeYawDeg:0,pipePitchDeg:0,pipeCurveDeg:(c.pipeCurveDeg||0)*(oldLength-distance)/oldLength,pipeCurveRollDeg:roll,weldTag:'W'+String(number).padStart(3,'0'),segmentBase:base,segmentGroup:group};
 delete second.hideInletWeld;
 c.lengthMM=distance;c.pipeCurveDeg=(c.pipeCurveDeg||0)*distance/oldLength;c.outletEnd='welded';c.segmentBase=base;c.segmentGroup=group;
 for(const child of d.components){if(child.parentPort===id+':out')child.parentPort=newId+':out';if(child.parentPort===id+':tap'&&child.tapOffsetMM>=distance){child.parentPort=newId+':tap';child.tapOffsetMM-=distance;}}
 for(const repair of d.repairs||[])if(repair.hostId===id&&repair.startMM>=distance){repair.hostId=newId;repair.startMM-=distance;}
 d.components.splice(d.components.indexOf(c)+1,0,second);d.components=sortComponents(d,catalog).components;
 let index=0;for(const part of d.components.filter(p=>p.segmentGroup===group))part.tag=base+'-'+String(++index).padStart(2,'0');
 // El primer cálculo usa las marcas antiguas solo como datos, luego se reproyectan.
 const after=compute(d,catalog);
 for(const a of d.annotations||[])if(points.has(a.id)){const s=a.coordinates[0]*oldLength;a.hostId=s>=distance?newId:id;a.coordinates=componentCoordinates(after.nodes.find(n=>n.id===a.hostId),points.get(a.id));}
 compute(d,catalog);return {design:d,newId,weldTag:second.weldTag};
}

// Quita una soldadura explícita. Unir exige conservar exactamente el recorrido.
export function removeWeld(design,id,catalog,join=true){
 const d=structuredClone(design),before=compute(d,catalog),b=d.components.find(c=>c.id===id);
 if(!b?.weldTag)throw Error('Selecciona un cordón de soldadura de la lista.');
 const weldTag=b.weldTag;
 if(!join){delete b.weldTag;b.hideInletWeld=true;return {design:d,id:b.id,weldTag};}
 const a=d.components.find(c=>b.parentPort===c.id+':out'),na=before.nodes.find(n=>n.id===a?.id),nb=before.nodes.find(n=>n.id===b.id);
 const near=(x,y,tolerance=1e-6)=>Math.hypot(...x.map((v,i)=>v-y[i]))<=tolerance;
 if(!a||a.kind!=='pipe'||b.kind!=='pipe'||a.outletEnd&&a.outletEnd!=='welded'||!['auto','welded',undefined].includes(b.inletEnd)||na.nps!==nb.nps||a.rating!==b.rating||!near(na.end,nb.start)||!near(na.endAxis,nb.axis))throw Error('Los tramos tienen geometrías o terminaciones distintas. Usa «Quitar solo cordón» para conservar sus formas.');
 const frame=pipeFrame(na,na.length),k1=(a.pipeCurveDeg||0)*Math.PI/180/a.lengthMM,k2=(b.pipeCurveDeg||0)*Math.PI/180/b.lengthMM;
 if(!near(frame.normal.map(v=>v*k1),nb.curveNormal.map(v=>v*k2),1e-10))throw Error('Las curvaturas son distintas. Usa «Quitar solo cordón» para conservar sus formas.');
 const points=new Map((d.annotations||[]).filter(x=>x.hostType==='component'&&[a.id,b.id].includes(x.hostId)).map(x=>[x.id,annotationPoint(x,before,d)])),offset=a.lengthMM;
 a.lengthMM+=b.lengthMM;a.pipeCurveDeg=(a.pipeCurveDeg||0)*a.lengthMM/offset;a.outletEnd=b.outletEnd||'welded';
 for(const child of d.components){if(child.parentPort===b.id+':out')child.parentPort=a.id+':out';if(child.parentPort===b.id+':tap'){child.parentPort=a.id+':tap';child.tapOffsetMM+=offset;}}
 for(const repair of d.repairs||[])if(repair.hostId===b.id){repair.hostId=a.id;repair.startMM+=offset;}
 for(const annotation of d.annotations||[])if(points.has(annotation.id))annotation.hostId=a.id;
 d.components=d.components.filter(c=>c.id!==b.id);if(d.lineColors)delete d.lineColors[b.id];
 d.components=sortComponents(d,catalog).components;
 const parts=d.components.filter(c=>c.segmentGroup&&c.segmentGroup===a.segmentGroup);for(const [i,part] of parts.entries())part.tag=parts.length===1?part.segmentBase:part.segmentBase+'-'+String(i+1).padStart(2,'0');
 const after=compute(d,catalog),merged=after.nodes.find(n=>n.id===a.id);
 if(!near(merged.end,nb.end)||!near(merged.endAxis,nb.endAxis))throw Error('No se pueden unir sin cambiar la forma. Usa «Quitar solo cordón».');
 for(const annotation of d.annotations||[])if(points.has(annotation.id))annotation.coordinates=componentCoordinates(merged,points.get(annotation.id));
 compute(d,catalog);return {design:d,id:a.id,weldTag};
}
