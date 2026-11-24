import {validateExternalObjects} from './external.mjs';
import {ponchoDimensions} from './poncho.mjs';
import {pipeHeading,pipeFrame} from './pipe_path.mjs';
import {validateDetails,repairRows} from './details.mjs';
import {connection,threadDetail} from './connections.mjs';
import {elbowSeat} from './elbow_surface.mjs';
import {equipmentPorts,validateEquipmentList} from './equipment.mjs';
// Motor de conexiones en mm. No depende del renderizador.
export const add=(a,b)=>a.map((v,i)=>v+b[i]);
export const sub=(a,b)=>a.map((v,i)=>v-b[i]);
export const mul=(v,s)=>v.map(x=>x*s);
export const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
export const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
export const norm=v=>mul(v,1/(Math.hypot(...v)||1));
export const TYPES={pipe:'Tramo recto',poncho:'Poncho de refuerzo',sockolet:'Sockolet · SW',thredolet:'Thredolet · NPT',latrolet:'Latrolet · 45°',elbolet:'Elbolet',elbow:'Codo',tee:'Tee',reducer:'Reductor BW',valve:'Válvula',flange:'Brida WN',cap:'Brida ciega',gauge:'Manómetro'};
export const VALVES={gate:'compuerta',ball:'bola',globe:'globo',check:'retención',butterfly:'mariposa',psv:'PSV · seguridad',rv:'RV · alivio'};
export const isOlet=c=>['sockolet','thredolet','latrolet','elbolet','poncho'].includes(c.kind);
export const isRelief=c=>c.kind==='valve'&&['psv','rv'].includes(c.valveType);
export const RATINGS=['150#','300#','600#'];
export function normal(axis,roll=0){let n=Math.abs(axis[1])<.85?[0,1,0]:[0,0,1];n=norm(sub(n,mul(axis,dot(n,axis))));const b=cross(axis,n),a=roll*Math.PI/180;return add(mul(n,Math.cos(a)),mul(b,Math.sin(a)));}
export function item(catalog,nps){const value=catalog.items.find(r=>r.nps===Number(nps));if(!value)throw Error('Medida nominal fuera del catálogo.');return value;}
export function blankDesign(id='piping-principal'){return {version:1,id,title:'Nueva línea de piping',direction:'+X',components:[],updatedAt:new Date().toISOString()};}
export function validateDesign(d,catalog){
 if(!d||d.version!==1||!Array.isArray(d.components)||d.components.length>200)throw Error('El archivo no es un diseño de piping válido (máximo 200 componentes).');
 // Los primeros diseños llamaban latrolet a la derivación de codo.
 for(const c of d.components)if(c?.kind==='latrolet'&&typeof c.parentPort==='string'&&d.components.some(host=>host?.id===c.parentPort?.split(':')[0]&&host.kind==='elbow'))c.kind='elbolet';
 const axes=['+X','-X','+Y','-Y','+Z','-Z'];if(!axes.includes(d.direction))throw Error('Dirección inicial inválida.');
 if(typeof d.id!=='string'||d.id.length>80||typeof d.title!=='string'||d.title.length>120)throw Error('Identificación de proyecto inválida.');
 validateExternalObjects(d.externalObjects);
 validateEquipmentList(d,catalog);const ids=new Set(),ports=new Set(['origin',...equipmentPorts(d,catalog).map(p=>p.id)]),used=new Set();
 for(const c of d.components){
  if(!c||typeof c.id!=='string'||!/^[a-zA-Z0-9_-]{1,64}$/.test(c.id)||ids.has(c.id)||!TYPES[c.kind])throw Error('Componente inválido o repetido.');
  if(!ports.has(c.parentPort)||(used.has(c.parentPort)&&!c.parentPort.endsWith(':tap'))||c.parentPort.endsWith(':tap')!==isOlet(c))throw Error('Hay una conexión inexistente u ocupada.');
  for(const field of ['nps','outNps','branchNps']){if(typeof c[field]!=='number'||!Number.isFinite(c[field]))throw Error('Medida nominal inválida.');item(catalog,c[field]);}
  if(!RATINGS.includes(c.rating)||typeof c.tag!=='string'||c.tag.length>40)throw Error('TAG o clase inválidos.');
  for(const [k,min,max] of [['lengthMM',10,100000],['radiusMM',10,100000],['branchLengthMM',10,100000],['rollDeg',-3600,3600]])if(typeof c[k]!=='number'||!Number.isFinite(c[k])||c[k]<min||c[k]>max)throw Error('Dimensión inválida: '+k);
  for(const [key,limit] of [['pipeXMM',100000],['pipeYMM',100000],['pipeZMM',100000],['pipeYawDeg',3600],['pipePitchDeg',90],['pipeCurveDeg',170],['pipeCurveRollDeg',3600]])if(c[key]!==undefined&&(typeof c[key]!=='number'||!Number.isFinite(c[key])||Math.abs(c[key])>limit))throw Error('Ángulo del tramo inválido: '+key);
  for(const key of ['segmentBase','segmentGroup'])if(c[key]!==undefined&&(typeof c[key]!=='string'||c[key].length>64))throw Error('Identificación de segmento inválida.');
  if(c.hideInletWeld!==undefined&&typeof c.hideInletWeld!=='boolean')throw Error('Visibilidad de soldadura inválida.');
  if(c.weldTag!==undefined&&(typeof c.weldTag!=='string'||c.weldTag.length>40))throw Error('Identificación de soldadura inválida.');
  if(c.kind==='pipe'&&c.parentPort==='origin')ports.add(c.id+':in');
  if(c.kind==='gauge'&&c.gaugeDiameterMM!==undefined&&(!Number.isFinite(c.gaugeDiameterMM)||c.gaugeDiameterMM<10||c.gaugeDiameterMM>100000))throw Error('Diámetro exterior del manómetro inválido.');
  if(![45,90].includes(c.bendAngle)||!['concentric','eccentric'].includes(c.reduction)||!Object.hasOwn(VALVES,c.valveType))throw Error('Configuración de accesorio inválida.');
  if(c.outletRating!==undefined&&!RATINGS.includes(c.outletRating))throw Error('Clase de salida inválida.');
  for(const key of ['outletEnd','branchEnd'])if(c[key]!==undefined&&!['welded','flanged','threaded','vent45'].includes(c[key]))throw Error('Terminación de extremo inválida.');
  if(c.kind==='elbolet'&&c.branchDirection!==undefined&&!['inlet','outlet','+X','-X','+Y','-Y','+Z','-Z','custom'].includes(c.branchDirection))throw Error('Dirección de derivación inválida.');
  if(c.kind==='elbolet')for(const [key,limit] of [['branchYawDeg',3600],['branchPitchDeg',90]])if(c[key]!==undefined&&(typeof c[key]!=='number'||!Number.isFinite(c[key])||Math.abs(c[key])>limit))throw Error('Giro de elbolet inválido.');
  if(c.kind==='elbolet'&&c.branchAngle!==undefined&&![45,90].includes(c.branchAngle))throw Error('Ángulo de derivación inválido.');
  if(isOlet(c)&&(typeof c.tapOffsetMM!=='number'||!Number.isFinite(c.tapOffsetMM)||c.tapOffsetMM<0))throw Error('Posición de sockolet inválida.');
  if(c.kind==='pipe'||c.kind==='elbow')ports.add(c.id+':tap');
  if(c.inletEnd!==undefined&&!['auto','welded','threaded'].includes(c.inletEnd)||c.valveConnection!==undefined&&!['flanged','threaded'].includes(c.valveConnection))throw Error('Tipo de conexión inválido.');
  if(c.outletEnd==='threaded'&&!['pipe','elbow'].includes(c.kind)||c.branchEnd==='threaded')throw Error('La terminación NPT está disponible para niples, codos y válvulas.');
  if(c.outletEnd==='vent45'&&c.kind!=='pipe'||c.branchEnd==='vent45')throw Error('El corte de venteo solo se admite en la salida de un niple.');
  if(c.kind==='tee'){if(!['a','b','branch'].includes(c.teeEntry??'a'))throw Error('Boca de entrada de tee inválida.');if(c.teeRunNps!==undefined)item(catalog,c.teeRunNps);if(c.parentPort==='origin')ports.add(c.id+':in');}
  ids.add(c.id);used.add(c.parentPort);if(!['cap','gauge'].includes(c.kind)&&c.outletEnd!=='vent45')ports.add(c.id+':out');if(c.kind==='tee')ports.add(c.id+':branch');
 }
 validateDetails(d);return d;
}
export function compute(d,catalog){
 validateDesign(d,catalog);
 const directions={'+X':[1,0,0],'-X':[-1,0,0],'+Y':[0,1,0],'-Y':[0,-1,0],'+Z':[0,0,1],'-Z':[0,0,-1]};
 const ports=new Map([['origin',{id:'origin',position:[0,0,0],axis:directions[d.direction],nps:null,endType:'plain',rating:null,label:'Inicio de la línea'}],...equipmentPorts(d,catalog).map(p=>[p.id,p])]),used=new Set(),nodes=[];
 for(const c of d.components){
  let origin=ports.get(c.parentPort);if(origin?.hostKind==='pipe'){const frame=pipeFrame(origin.pipeNode,c.tapOffsetMM||0);origin={...origin,position:frame.point,axis:frame.axis,radialAxis:frame.normal};}const {inletType,femaleThreaded}=connection(c,origin);const inletNps=origin.nps??c.nps,nps=c.kind==='tee'&&c.teeEntry==='branch'?(c.teeRunNps??inletNps):inletNps,pipe=item(catalog,nps),rating=origin.endType==='flanged'?origin.rating:c.rating,flange=origin.endType==='flanged'&&origin.flangeSpec?origin.flangeSpec:item(catalog,inletNps).flanges[rating];
  if(isOlet(c)){
   if((c.kind==='elbolet')!==(origin.hostKind==='elbow')||c.tapOffsetMM>origin.runLengthMM||c.outNps>nps)throw Error('El sockolet debe quedar dentro del tramo y su salida no puede superar la línea principal.');
   const roll=c.rollDeg*Math.PI/180,radial=origin.radialAxis?add(mul(origin.radialAxis,Math.cos(roll)),mul(cross(origin.axis,origin.radialAxis),Math.sin(roll))):normal(origin.axis,c.rollDeg),direction=c.branchDirection||(c.branchAngle===45?'inlet':'outlet'),yaw=(c.branchYawDeg||0)*Math.PI/180,pitch=(c.branchPitchDeg||0)*Math.PI/180,branchAxis=c.kind==='elbolet'?(directions[direction]?[...directions[direction]]:direction==='custom'?[Math.cos(pitch)*Math.cos(yaw),Math.cos(pitch)*Math.sin(yaw),Math.sin(pitch)]:[...(direction==='inlet'?origin.inletAxis:origin.outletAxis)]):c.kind==='latrolet'?norm(add(origin.axis,radial)):radial,projection=c.kind==='elbolet'?Math.max(.1,Math.sqrt(Math.max(0,1-dot(branchAxis,origin.axis)**2))):c.kind==='latrolet'?Math.SQRT1_2:1,center=add(origin.position,mul(origin.axis,origin.hostKind==='pipe'?0:c.tapOffsetMM)),start=add(center,mul(branchAxis,c.kind==='elbolet'?elbowSeat(center,branchAxis,origin.elbowSurface):pipe.odMM/(2*projection))),end=add(start,mul(branchAxis,c.lengthMM));
   const pad=c.kind==='poncho'?ponchoDimensions(c,pipe.odMM,item(catalog,c.outNps).odMM,origin.runLengthMM):undefined;
   const node={...c,pad,nps,rating,start,end,axis:branchAxis,endAxis:branchAxis,normal:normal(branchAxis),center:mul(add(start,end),.5),length:c.lengthMM,flange,odMM:pipe.odMM,endNps:c.outNps,endType:c.kind==='thredolet'?'threaded':'plain',endRating:rating,origin,runCenter:center};nodes.push(node);ports.set(c.id+':out',{id:c.id+':out',position:end,axis:branchAxis,nps:c.outNps,endType:c.kind==='thredolet'?'threaded':'plain',threadGender:c.kind==='thredolet'?'female':undefined,rating,label:c.tag+(c.kind==='thredolet'?' · salida roscada NPT':' · salida soldada')});continue;
  }
  const axis=c.kind==='pipe'?pipeHeading(origin.axis,c.pipeYawDeg||0,c.pipePitchDeg||0):origin.axis,n=normal(axis,c.rollDeg);let start=[...origin.position],adapter=null,reverse=false;
  if(c.kind==='pipe'&&c.parentPort==='origin')start=add(start,[c.pipeXMM||0,c.pipeYMM||0,c.pipeZMM||0]);
  // Bridas contraparte automáticas al conectar un extremo enflanchado.
  if(femaleThreaded||inletType==='threaded'){/* Unión NPT, sin bridas ni contraparte automática. */}
  else if(c.kind==='flange'&&origin.endType==='flanged'){start=add(start,mul(axis,3));reverse=true;}
  else if(c.kind==='valve'||c.kind==='cap'){
   if(origin.id!=='origin'&&origin.endType==='plain'){adapter={start:[...start],axis:[...axis],reverse:false,flange,nps:inletNps,rating};start=add(start,mul(axis,flange.lengthMM+3));}
   else if(origin.endType==='flanged')start=add(start,mul(axis,3));
  }else if(origin.endType==='flanged'){
   const seat=add(start,mul(axis,3));adapter={start:add(seat,mul(axis,flange.lengthMM)),axis:mul(axis,-1),reverse:true,flange,nps:inletNps,rating};start=add(seat,mul(axis,flange.lengthMM));
  }
  let end=add(start,mul(axis,c.lengthMM)),endAxis=axis,endNps=nps,endType='plain',branch=null,center=add(start,mul(axis,c.lengthMM/2)),length=c.lengthMM,teeA=null,teeB=null,teeLegEnd=null,teeEntry=c.teeEntry||'a',effectiveBranchNps=c.branchNps,endRating=rating,outletFlange=null;
  if(c.kind==='pipe'){const curveNormal=normal(axis,c.pipeCurveRollDeg||0),shape={...c,start,axis,normal:n,curveNormal,length};if(c.pipeCurveDeg&&length/(Math.abs(c.pipeCurveDeg)*Math.PI/180)<=pipe.odMM/2)throw Error('La curva necesita un radio mayor al radio exterior del tubo.');const last=pipeFrame(shape,length);end=last.point;endAxis=last.axis;center=pipeFrame(shape,length/2).point;
  }else if(c.kind==='elbow'){
   const a=c.bendAngle*Math.PI/180,R=Math.max(c.radiusMM,pipe.odMM*.6);length=R*a;
   const point=t=>add(start,add(mul(axis,R*Math.sin(a*t)),mul(n,R*(1-Math.cos(a*t)))));
   end=point(1);center=point(.5);endAxis=norm(add(mul(axis,Math.cos(a)),mul(n,Math.sin(a))));
  }else if(c.kind==='tee'){
   effectiveBranchNps=teeEntry==='branch'?inletNps:c.branchNps;
   if(effectiveBranchNps>nps)throw Error('La derivación de la tee no puede superar la medida principal.');
   const runAxis=teeEntry==='branch'?n:teeEntry==='b'?mul(axis,-1):axis;
   center=add(start,mul(axis,teeEntry==='branch'?c.branchLengthMM:c.lengthMM/2));teeA=sub(center,mul(runAxis,c.lengthMM/2));teeB=add(center,mul(runAxis,c.lengthMM/2));teeLegEnd=teeEntry==='branch'?start:add(center,mul(n,c.branchLengthMM));
   end=teeEntry==='a'?teeB:teeA;endAxis=teeEntry==='a'?runAxis:mul(runAxis,-1);endNps=nps;
   branch={id:c.id+':branch',position:teeEntry==='branch'?teeB:teeLegEnd,axis:teeEntry==='branch'?runAxis:n,nps:teeEntry==='branch'?nps:effectiveBranchNps,endType:'plain',rating,label:c.tag+(teeEntry==='branch'?' · lado B':' · derivación')};
  }else if(c.kind==='reducer'){
   endNps=c.outNps;if(c.reduction==='eccentric')end=add(end,mul(n,(pipe.odMM-item(catalog,endNps).odMM)/2));
   center=mul(add(start,end),.5);
  }else if(c.kind==='flange'){
   length=flange.lengthMM;end=add(start,mul(axis,length));center=mul(add(start,end),.5);endType=reverse?'plain':'flanged';
  }else if(c.kind==='valve'){
   if(isRelief(c)){
    length=Math.max(c.lengthMM,flange.lengthMM+pipe.odMM*4.5);const bodyHeight=Math.max(flange.lengthMM+pipe.odMM*.8,length*.27);center=add(start,mul(axis,bodyHeight));endNps=c.outNps;endRating=c.outletRating||rating;outletFlange=item(catalog,endNps).flanges[endRating];const sideLength=Math.max(c.branchLengthMM,outletFlange.lengthMM+pipe.odMM*.9);end=add(center,mul(n,sideLength));endAxis=n;
   }else{length=Math.max(c.lengthMM,flange.lengthMM*2+pipe.odMM*1.3);end=add(start,mul(axis,length));center=mul(add(start,end),.5);}endType=femaleThreaded?'threaded':'flanged';
  }else if(c.kind==='gauge'){
   const dialRadius=c.gaugeDiameterMM===undefined?Math.max(32,pipe.odMM*.9):c.gaugeDiameterMM/2;
   length=dialRadius*2+pipe.odMM*.85;
   center=add(start,mul(axis,length-dialRadius));
   end=add(start,mul(axis,length));
   endType='closed';
  }else if(c.kind==='cap'){
   length=flange.thicknessMM;end=add(start,mul(axis,length));center=mul(add(start,end),.5);endType='closed';
  }
  if(['pipe','elbow'].includes(c.kind)&&c.outletEnd==='threaded')endType='threaded';
  if(c.outletEnd==='vent45'){
   if(length<=pipe.odMM/2)throw Error('El largo del niple de venteo debe superar el radio exterior.');
   endType='vent45';
  }
  let outletEndFlange=null;if(['pipe','elbow','tee','reducer'].includes(c.kind)&&c.outletEnd==='flanged'){outletEndFlange=item(catalog,endNps).flanges[rating];endType='flanged';}
  if(branch&&c.branchEnd==='flanged'){branch.flangeSpec=item(catalog,branch.nps).flanges[rating];branch.bodyPosition=[...branch.position];branch.position=add(branch.position,mul(branch.axis,branch.flangeSpec.lengthMM));branch.endType='flanged';}
  const node={...c,curveNormal:normal(axis,c.pipeCurveRollDeg||0),nps,rating,start,end,axis,endAxis,inletType,normal:n,center,length,flange,odMM:pipe.odMM,endNps,endType,endRating,outletFlange,outletEndFlange,teeA,teeB,teeLegEnd,teeEntry,branchNps:effectiveBranchNps,branch,adapter,reverse,origin};nodes.push(node);used.add(c.parentPort);
  if(!['cap','gauge'].includes(c.kind)&&c.outletEnd!=='vent45')ports.set(c.id+':out',{id:c.id+':out',position:outletEndFlange?add(end,mul(endAxis,outletEndFlange.lengthMM)):end,axis:endAxis,nps:endNps,endType,threadGender:endType==='threaded'?(c.kind==='pipe'?'male':'female'):undefined,rating:endRating,flangeSpec:outletEndFlange||(c.kind==='valve'?(outletFlange||flange):undefined),label:c.tag+(c.kind==='tee'?(teeEntry==='a'?' · lado B':' · lado A'):' · salida principal')});
  if(['tee','pipe'].includes(c.kind)&&origin.id==='origin')ports.set(c.id+':in',{id:c.id+':in',position:start,axis:mul(axis,-1),nps:inletNps,endType:'plain',rating,label:c.tag+(c.kind==='pipe'?' · inicio':teeEntry==='branch'?' · derivación':teeEntry==='b'?' · lado B':' · lado A')});
  if(c.kind==='elbow'){const a=c.bendAngle*Math.PI/360,tangent=norm(add(mul(axis,Math.cos(a)),mul(n,Math.sin(a))));ports.set(c.id+':tap',{id:c.id+':tap',position:center,axis:tangent,inletAxis:[...axis],outletAxis:[...endAxis],radialAxis:sub(mul(axis,Math.sin(a)),mul(n,Math.cos(a))),nps,endType:'run',rating,runLengthMM:0,hostKind:'elbow',elbowSurface:{start:[...start],axis:[...axis],normal:[...n],radiusMM:Math.max(c.radiusMM,pipe.odMM*.6),angleRad:c.bendAngle*Math.PI/180,odMM:pipe.odMM},label:c.tag+' · centro del codo'});}
  if(c.kind==='pipe')ports.set(c.id+':tap',{hostKind:'pipe',pipeNode:node,id:c.id+':tap',position:start,axis,nps,endType:'run',rating,runLengthMM:c.lengthMM,label:c.tag+' · línea principal'});
  if(branch)ports.set(branch.id,branch);
 }
 const freePorts=[...ports.values()].filter(p=>!used.has(p.id)&&p.endType!=='run');return {nodes,ports,freePorts,repairs:d.repairs||[],annotations:d.annotations||[]};
}
export function descendants(d,id){const ids=new Set([id]);let change=true;while(change){change=false;for(const c of d.components)if(ids.has(c.parentPort.split(':')[0])&&!ids.has(c.id)){ids.add(c.id);change=true;}}return ids;}
export function materialRows(result,catalog){
 const rows=new Map();function push(kind,nps,rating,outNps=0,length=0,detail='',termination=''){
  const label=TYPES[kind]+(kind==='elbow'?' '+detail+'°':kind==='valve'?' '+(VALVES[detail]||detail):kind==='reducer'?' '+(detail==='eccentric'?'excéntrico':'concéntrico'):'')+termination,measure=item(catalog,nps).label+(outNps?' × '+item(catalog,outNps).label:'');
  const cls=rating==='NPT'||['flange','valve','cap'].includes(kind)?rating:'—',key=[label,measure,cls].join('|');if(!rows.has(key))rows.set(key,{description:label,nps:measure,rating:cls,quantity:0,lengthMM:0});const row=rows.get(key);row.quantity++;if(kind==='pipe')row.lengthMM+=length;
 }
 for(const n of result.nodes){if(n.adapter)push('flange',n.adapter.nps,n.rating);if(n.outletEndFlange)push('flange',n.endNps,n.rating);if(n.branch?.flangeSpec)push('flange',n.branch.nps,n.rating);push(n.kind,n.nps,n.kind==='gauge'||n.endType==='threaded'&&['valve','elbow'].includes(n.kind)?'NPT':isRelief(n)?n.rating+' / '+n.endRating:n.rating,n.kind==='reducer'||isOlet(n)||isRelief(n)?n.outNps:n.kind==='tee'&&n.branchNps!==n.nps?n.branchNps:0,n.length,n.kind==='elbow'?n.bendAngle:n.kind==='valve'?n.valveType:n.reduction,threadDetail(n,n.inletType,n.endType)+(n.kind==='poncho'?' · L '+n.pad.length+' mm · e '+n.pad.thickness+' mm · '+n.pad.coverage+'°':''));}
 return [...rows.values(),...repairRows(result,catalog)];
}
