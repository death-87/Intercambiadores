import {pipeFrame,pipeDistance} from './pipe_path.mjs';
const add=(a,b)=>a.map((x,i)=>x+b[i]),mul=(a,k)=>a.map(x=>x*k),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
export const REPAIRS={type_b:'Camisa Tipo B · soldada',patch:'Parche soldado'};
export const DEFAULT_PATCH_COLOR='#c48c32';
export const COLORS=['#c74336','#276caa','#16846a','#d28a24'];
export function validateDetails(d){
 const components=new Map(d.components.filter(c=>c&&typeof c.id==='string').map(c=>[c.id,c])),equipment=new Set((d.equipments||[]).map(e=>e.id));
 for(const [key,max] of [['repairs',100],['annotations',100]]){const values=d[key]??[];if(!Array.isArray(values)||values.length>max)throw Error('Se admiten hasta 100 reparaciones y 100 marcas.');const ids=new Set();
  for(const x of values){if(!x||typeof x.id!=='string'||!/^[a-zA-Z0-9_-]{1,64}$/.test(x.id)||ids.has(x.id))throw Error('Identificación de reparación o marca inválida.');ids.add(x.id);
   const text=(value,limit)=>typeof value==='string'&&value.length<=limit;
   if(key==='repairs'){
    const host=components.get(x.hostId);if(!host||host.kind!=='pipe'||!Object.hasOwn(REPAIRS,x.type)||!text(x.tag,40)||!text(x.comment,500))throw Error('La reparación necesita un tramo recto y una identificación válida.');
    for(const [name,min,max] of [['startMM',0,100000],['lengthMM',10,100000],['thicknessMM',.5,100],['coverageDeg',10,300],['rollDeg',-3600,3600]])if(typeof x[name]!=='number'||!Number.isFinite(x[name])||x[name]<min||x[name]>max)throw Error('Dimensión de reparación inválida: '+name);
    if(Object.hasOwn(x,'color')&&(typeof x.color!=='string'||!/^#[0-9a-f]{6}$/i.test(x.color)))throw Error('Color de parche inválido.');
    if(x.startMM+x.lengthMM>host.lengthMM+.001)throw Error('La reparación debe quedar dentro del largo del tramo.');
   }else{
    if(!['component','equipment'].includes(x.hostType)||!(x.hostType==='component'?components.has(x.hostId):equipment.has(x.hostId))||!Array.isArray(x.coordinates)||x.coordinates.length!==3||x.coordinates.some(v=>typeof v!=='number'||!Number.isFinite(v)||Math.abs(v)>1e6)||!text(x.number,20)||!text(x.text,500)||!COLORS.includes(x.color)||!['both','arrow','circle'].includes(x.style))throw Error('Marca o punto de referencia inválido.');
    for(const k of ['offsetX','offsetY'])if(typeof x[k]!=='number'||!Number.isFinite(x[k])||Math.abs(x[k])>800)throw Error('Desplazamiento de marca inválido.');
   }
  }
 }
}
export function componentFrame(node){const radius=node.odMM/2;return {origin:node.start,axes:[node.axis,node.normal,cross(node.axis,node.normal)],scale:[Math.max(node.length,10),node.kind==='elbow'?Math.max(node.radiusMM,radius):node.kind==='tee'?Math.max(node.branchLengthMM,radius):radius,radius]};}
export function componentCoordinates(node,point){if(node.kind==='pipe'&&node.pipeCurveDeg){const s=pipeDistance(node,point),f=pipeFrame(node,s),q=point.map((x,i)=>x-f.point[i]);return [s/node.length,dot(q,f.normal)/(node.odMM/2),dot(q,f.binormal)/(node.odMM/2)];}const f=componentFrame(node),q=point.map((x,i)=>x-f.origin[i]);return f.axes.map((a,i)=>dot(q,a)/f.scale[i]);}
export function annotationPoint(annotation,result,design){
 if(annotation.hostType==='component'){const node=result.nodes.find(n=>n.id===annotation.hostId);if(node.kind==='pipe'&&node.pipeCurveDeg){const [t,y,z]=annotation.coordinates,f=pipeFrame(node,t*node.length);return add(f.point,add(mul(f.normal,y*node.odMM/2),mul(f.binormal,z*node.odMM/2)));}const f=componentFrame(node);return annotation.coordinates.reduce((p,value,i)=>add(p,mul(f.axes[i],value*f.scale[i])),[...f.origin]);}
 const e=design.equipments.find(e=>e.id===annotation.hostId),a=e.rotationDeg*Math.PI/180,[x,y,z]=annotation.coordinates;return add([Math.cos(a)*x-Math.sin(a)*y,Math.sin(a)*x+Math.cos(a)*y,z],e.position);
}
export function removeDetails(d,componentIds,equipmentIds=new Set()){
 d.repairs=(d.repairs||[]).filter(r=>!componentIds.has(r.hostId));d.annotations=(d.annotations||[]).filter(a=>!(a.hostType==='component'?componentIds:equipmentIds).has(a.hostId));
}
export function repairRows(result,catalog){const rows=[];for(const repair of result.repairs||[]){const node=result.nodes.find(n=>n.id===repair.hostId),measure=catalog.items.find(r=>r.nps===node.nps).label;rows.push({description:REPAIRS[repair.type]+' · '+repair.tag,nps:measure+' · e '+repair.thicknessMM+' mm',rating:'—',quantity:1,lengthMM:repair.lengthMM});}return rows;}
