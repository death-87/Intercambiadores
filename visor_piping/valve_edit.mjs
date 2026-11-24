import {compute,item} from './model.mjs';
import {sortComponents} from './equipment.mjs';
// Cambio atómico de conexión: actualizar niples o intercalar los necesarios.
export function adaptValveEdit(design,id,catalog){
 const valve=design.components.find(c=>c.id===id);if(valve?.kind!=='valve')return design;
 const threaded=valve.valveConnection==='threaded';let seq=0;
 function nipple(parentPort,outletEnd,nps){let key;do{key=id.slice(0,48)+'_npt_'+(++seq);}while(design.components.some(c=>c.id===key));const c={...valve,id:key,tag:('N-'+valve.tag+'-'+seq).slice(0,40),kind:'pipe',parentPort,nps,outNps:nps,branchNps:nps,lengthMM:Math.max(100,item(catalog,nps).odMM),inletEnd:'auto',outletEnd,teeEntry:'a',teeRunNps:nps};design.components.push(c);return c;}
 const parent=design.components.find(c=>valve.parentPort===c.id+':out');
 if(parent?.kind==='pipe'){parent.outletEnd=threaded?'threaded':'welded';}
 else if(valve.parentPort!=='origin'){
  const before=structuredClone(design);before.components=before.components.filter(c=>c.id!==id&&!descendant(c,id,design));let port;
  try{port=compute(sortComponents(before,catalog),catalog).ports.get(valve.parentPort);}catch{port=null;}
  if(port&&(threaded?port.endType!=='threaded'||port.threadGender!=='male':port.endType==='threaded')){const extra=nipple(valve.parentPort,threaded?'threaded':'welded',port.nps);valve.parentPort=extra.id+':out';}
 }
 for(const child of [...design.components].filter(c=>c.parentPort===id+':out')){
  if(child.kind==='pipe')child.inletEnd='auto';
  else if(threaded||child.kind==='valve'&&child.valveConnection==='threaded'){const nps=['psv','rv'].includes(valve.valveType)?valve.outNps:valve.nps,extra=nipple(id+':out',child.kind==='valve'&&child.valveConnection==='threaded'?'threaded':'welded',nps);child.parentPort=extra.id+':out';}
 }
 design.components=sortComponents(design,catalog).components;return design;
}
function descendant(c,id,d){let current=c;const seen=new Set();while(current&&!seen.has(current.id)){seen.add(current.id);const p=current.parentPort?.split(':')[0];if(p===id)return true;current=d.components.find(n=>n.id===p);}return false;}
