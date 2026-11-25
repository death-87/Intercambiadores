import {compute,isOlet,item,TYPES} from './model.mjs';
import {sortComponents} from './equipment.mjs';
import {adaptValveEdit} from './valve_edit.mjs';
export const REPLACEMENTS=[{value:'elbowLR',kind:'elbow',longRadius:true,label:'Codo LR · ASME B16.9'},{value:'psv',kind:'valve',valveType:'psv',label:'Válvula PSV · seguridad'},{value:'rv',kind:'valve',valveType:'rv',label:'Válvula RV · alivio'},...Object.keys(TYPES).filter(k=>k!=='reducer').map(kind=>({value:kind,kind,label:TYPES[kind]})),{value:'reducer-concentric',kind:'reducer',reduction:'concentric',label:'Reducción concéntrica BW'},{value:'reducer-eccentric',kind:'reducer',reduction:'eccentric',label:'Reducción excéntrica BW'}];
export function replaceComponent(design,id,value,catalog){
 const choice=REPLACEMENTS.find(x=>x.value===value);if(!choice)throw Error('Elige un tipo de componente válido.');
 const d=structuredClone(design),before=compute(d,catalog),c=d.components.find(c=>c.id===id),node=before.nodes.find(n=>n.id===id);if(!c)throw Error('Selecciona un componente.');
 const wasOlet=isOlet(c),oldKind=c.kind,wasThreaded=c.valveConnection==='threaded';
 if(wasOlet!==isOlet(choice))throw Error('Una derivación sobre el tubo debe reemplazarse por otra derivación; un elemento en línea, por otro elemento en línea.');
 c.kind=choice.kind;delete c.longRadius;
 if(choice.longRadius)c.longRadius=true;
 if(choice.kind==='flangeSW'&&oldKind!=='flangeSW')c.lengthMM=item(catalog,node.nps).flanges[node.rating].lengthMM;
if(choice.reduction)c.reduction=choice.reduction;if(choice.valveType)c.valveType=choice.valveType;
 // Mantener el host y la boca del ramal; nunca cambiar a otra línea en silencio.
 if(c.kind==='poncho'&&oldKind!=='poncho'){
  const host=before.nodes.find(n=>n.id===c.parentPort.split(':')[0]);if(host?.kind!=='pipe')throw Error('El poncho requiere un tramo de tubo principal.');
  const branchOD=item(catalog,c.outNps).odMM,available=2*Math.min(c.tapOffsetMM,host.length-c.tapOffsetMM);
  c.padLengthMM=Math.min(Math.max(250,branchOD*2),available);c.padThicknessMM=6;c.padCoverageDeg=160;
  c.lengthMM=Math.max(c.lengthMM,10);
 }
 if(c.kind==='elbolet'&&oldKind!=='elbolet'){c.tapOffsetMM=0;c.branchDirection='outlet';}
 if(c.kind==='valve'&&oldKind!=='valve'){c.valveType=choice.valveType||'gate';c.valveConnection=node.inletType==='threaded'?'threaded':'flanged';}
 // Cambiar válvula a un tubo mantiene el extremo necesario para su continuación.
 if(c.kind==='pipe'&&oldKind==='valve'){c.inletEnd=wasThreaded?'threaded':'auto';c.outletEnd=wasThreaded?'threaded':'flanged';}
 try{
  if(oldKind==='valve'&&c.kind==='valve'&&wasThreaded!==(c.valveConnection==='threaded'))adaptValveEdit(d,id,catalog);
  d.components=sortComponents(d,catalog).components;compute(d,catalog);
 }catch(error){throw Error('No se puede reemplazar conservando las conexiones actuales: '+error.message);}
 return d;
}
