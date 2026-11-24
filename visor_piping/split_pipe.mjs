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
