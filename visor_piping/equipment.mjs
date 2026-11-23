// Activos y puertos del ensamblaje. Coordenadas mm; Z vertical.
const add=(a,b)=>a.map((v,i)=>v+b[i]);const norm=v=>{const l=Math.hypot(...v);return v.map(x=>x/l);};const RATINGS=['150#','300#','600#'];function item(catalog,nps){if(!catalog.items.some(r=>r.nps===nps))throw Error('Medida de boquilla fuera del catálogo.');}
export function equipmentPortId(equipment,port){return 'eq-'+equipment.id+'/'+port.id;}
export function equipmentPorts(design,catalog){
 const ports=[];
 for(const e of design.equipments||[]){const a=(e.rotationDeg||0)*Math.PI/180,c=Math.cos(a),s=Math.sin(a),rotate=p=>[c*p[0]-s*p[1],s*p[0]+c*p[1],p[2]];
  for(const p of e.ports){item(catalog,p.nps);ports.push({...p,id:equipmentPortId(e,p),position:add(rotate(p.position),e.position),axis:norm(rotate(p.axis)),endType:'flanged',equipmentId:e.id,label:e.tag+' · '+p.tag});}
 }
 return ports;
}
export function validateEquipmentList(design,catalog){
 if(design.equipments?.length&&JSON.stringify(design).length>30000000)throw Error('El ensamblaje supera el tamaño de respaldo admitido.');
 const equipments=design.equipments||[];if(!Array.isArray(equipments)||equipments.length>6)throw Error('El ensamblaje admite hasta 6 equipos.');const ids=new Set();
 for(const e of equipments){
  if(!e||typeof e.id!=='string'||!/^[a-zA-Z0-9_-]{1,64}$/.test(e.id)||ids.has(e.id)||typeof e.tag!=='string'||!e.tag.trim()||e.tag.length>80)throw Error('Identificación de equipo inválida.');ids.add(e.id);
  if(!Array.isArray(e.position)||e.position.length!==3||e.position.some(v=>typeof v!=='number'||!Number.isFinite(v)||Math.abs(v)>1e6)||typeof e.rotationDeg!=='number'||!Number.isFinite(e.rotationDeg)||Math.abs(e.rotationDeg)>3600)throw Error('Posición de equipo inválida.');
  if(e.nameplate&&(!Array.isArray(e.nameplate.matrix)||e.nameplate.matrix.length!==16||e.nameplate.matrix.some(x=>typeof x!=='number'||!Number.isFinite(x)||Math.abs(x)>1e6)))throw Error('Posición de nameplate inválida.');
  if(!e.asset||e.asset.format!=='three-buffer-v1'||!e.asset.data?.object||JSON.stringify(e.asset).length>16000000)throw Error('Geometría del equipo inválida o demasiado grande.');
  if(!Array.isArray(e.ports)||e.ports.length>200)throw Error('Puertos de equipo inválidos.');const ports=new Set();
  for(const p of e.ports){if(typeof p.id!=='string'||!/^[a-zA-Z0-9_-]{1,64}$/.test(p.id)||ports.has(p.id)||typeof p.tag!=='string'||p.tag.length>80||!RATINGS.includes(p.rating))throw Error('Boquilla de equipo inválida.');ports.add(p.id);item(catalog,p.nps);
   for(const field of ['position','axis'])if(!Array.isArray(p[field])||p[field].length!==3||p[field].some(x=>typeof x!=='number'||!Number.isFinite(x)||Math.abs(x)>1e6))throw Error('Coordenadas de boquilla inválidas.');if(Math.hypot(...p.axis)<.01)throw Error('La dirección de boquilla no puede ser nula.');
   if(p.flangeSpec){const f=p.flangeSpec;for(const k of ['diameterMM','thicknessMM','hubDiameterMM','lengthMM','pitchMM','holeMM','odMM','raisedFaceMM'])if(typeof f[k]!=='number'||!Number.isFinite(f[k])||f[k]<=0||f[k]>10000)throw Error('Dimensión de brida de equipo inválida.');if(!Number.isInteger(f.boltCount)||f.boltCount<4||f.boltCount>120)throw Error('Pernos de brida inválidos.');}
  }
 }
 return equipments;
}
export function sortComponents(design,catalog){
 const available=new Set(['origin',...equipmentPorts(design,catalog).map(p=>p.id)]),ordered=[],pending=[...design.components];
 while(pending.length){let progress=false;for(let i=0;i<pending.length;){const c=pending[i];if(available.has(c.parentPort)){ordered.push(c);if(c.kind!=='cap')available.add(c.id+':out');if(c.kind==='pipe'||c.kind==='elbow')available.add(c.id+':tap');if(c.kind==='tee'){available.add(c.id+':branch');if(c.parentPort==='origin')available.add(c.id+':in');}pending.splice(i,1);progress=true;}else i++;}if(!progress)throw Error('No se puede acoplar: la conexión crearía un ciclo o usa una boquilla inexistente.');}
 return {...design,components:ordered};
}
