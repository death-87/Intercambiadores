// Motor de conexiones en mm. No depende del renderizador.
export const add=(a,b)=>a.map((v,i)=>v+b[i]);
export const sub=(a,b)=>a.map((v,i)=>v-b[i]);
export const mul=(v,s)=>v.map(x=>x*s);
export const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
export const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
export const norm=v=>mul(v,1/(Math.hypot(...v)||1));
export const TYPES={pipe:'Tramo recto',elbow:'Codo',tee:'Tee',reducer:'Reductor',valve:'Válvula',flange:'Brida WN',cap:'Brida ciega'};
export const RATINGS=['150#','300#','600#'];
export function normal(axis,roll=0){let n=Math.abs(axis[1])<.85?[0,1,0]:[0,0,1];n=norm(sub(n,mul(axis,dot(n,axis))));const b=cross(axis,n),a=roll*Math.PI/180;return add(mul(n,Math.cos(a)),mul(b,Math.sin(a)));}
export function item(catalog,nps){const value=catalog.items.find(r=>r.nps===Number(nps));if(!value)throw Error('Medida nominal fuera del catálogo.');return value;}
export function blankDesign(id='piping-principal'){return {version:1,id,title:'Nueva línea de piping',direction:'+X',components:[],updatedAt:new Date().toISOString()};}
export function validateDesign(d,catalog){
 if(!d||d.version!==1||!Array.isArray(d.components)||d.components.length>200)throw Error('El archivo no es un diseño de piping válido (máximo 200 componentes).');
 const axes=['+X','-X','+Y','-Y','+Z','-Z'];if(!axes.includes(d.direction))throw Error('Dirección inicial inválida.');
 if(typeof d.id!=='string'||d.id.length>80||typeof d.title!=='string'||d.title.length>120)throw Error('Identificación de proyecto inválida.');
 const ids=new Set(),ports=new Set(['origin']),used=new Set();
 for(const c of d.components){
  if(!c||typeof c.id!=='string'||!/^[a-zA-Z0-9_-]{1,64}$/.test(c.id)||ids.has(c.id)||!TYPES[c.kind])throw Error('Componente inválido o repetido.');
  if(!ports.has(c.parentPort)||used.has(c.parentPort))throw Error('Hay una conexión inexistente u ocupada.');
  for(const field of ['nps','outNps','branchNps']){if(typeof c[field]!=='number'||!Number.isFinite(c[field]))throw Error('Medida nominal inválida.');item(catalog,c[field]);}
  if(!RATINGS.includes(c.rating)||typeof c.tag!=='string'||c.tag.length>40)throw Error('TAG o clase inválidos.');
  for(const [k,min,max] of [['lengthMM',10,100000],['radiusMM',10,100000],['branchLengthMM',10,100000],['rollDeg',-3600,3600]])if(typeof c[k]!=='number'||!Number.isFinite(c[k])||c[k]<min||c[k]>max)throw Error('Dimensión inválida: '+k);
  if(![45,90].includes(c.bendAngle)||!['concentric','eccentric'].includes(c.reduction)||!['gate','ball'].includes(c.valveType))throw Error('Configuración de accesorio inválida.');
  ids.add(c.id);used.add(c.parentPort);if(c.kind!=='cap')ports.add(c.id+':out');if(c.kind==='tee')ports.add(c.id+':branch');
 }
 return d;
}
export function compute(d,catalog){
 validateDesign(d,catalog);
 const directions={'+X':[1,0,0],'-X':[-1,0,0],'+Y':[0,1,0],'-Y':[0,-1,0],'+Z':[0,0,1],'-Z':[0,0,-1]};
 const ports=new Map([['origin',{id:'origin',position:[0,0,0],axis:directions[d.direction],nps:null,endType:'plain',rating:null,label:'Inicio de la línea'}]]),used=new Set(),nodes=[];
 for(const c of d.components){
  const origin=ports.get(c.parentPort),nps=origin.nps??c.nps,pipe=item(catalog,nps),rating=origin.endType==='flanged'?origin.rating:c.rating,flange=pipe.flanges[rating];
  const axis=origin.axis,n=normal(axis,c.rollDeg);let start=[...origin.position],adapter=null,reverse=false;
  // Bridas contraparte automáticas al conectar un extremo enflanchado.
  if(c.kind==='flange'&&origin.endType==='flanged'){start=add(start,mul(axis,3));reverse=true;}
  else if(c.kind==='valve'||c.kind==='cap'){
   if(origin.id!=='origin'&&origin.endType==='plain'){adapter={start:[...start],axis:[...axis],reverse:false,flange,nps,rating};start=add(start,mul(axis,flange.lengthMM+3));}
   else if(origin.endType==='flanged')start=add(start,mul(axis,3));
  }else if(origin.endType==='flanged'){
   const seat=add(start,mul(axis,3));adapter={start:add(seat,mul(axis,flange.lengthMM)),axis:mul(axis,-1),reverse:true,flange,nps,rating};start=add(seat,mul(axis,flange.lengthMM));
  }
  let end=add(start,mul(axis,c.lengthMM)),endAxis=axis,endNps=nps,endType='plain',branch=null,center=add(start,mul(axis,c.lengthMM/2)),length=c.lengthMM;
  if(c.kind==='elbow'){
   const a=c.bendAngle*Math.PI/180,R=Math.max(c.radiusMM,pipe.odMM*.6);length=R*a;
   const point=t=>add(start,add(mul(axis,R*Math.sin(a*t)),mul(n,R*(1-Math.cos(a*t)))));
   end=point(1);center=point(.5);endAxis=norm(add(mul(axis,Math.cos(a)),mul(n,Math.sin(a))));
  }else if(c.kind==='tee'){
   if(c.branchNps>nps)throw Error('La derivación de la tee no puede superar la medida de entrada.');
   branch={id:c.id+':branch',position:add(center,mul(n,c.branchLengthMM)),axis:n,nps:c.branchNps,endType:'plain',rating,label:c.tag+' · derivación'};
  }else if(c.kind==='reducer'){
   endNps=c.outNps;if(c.reduction==='eccentric')end=add(end,mul(n,(pipe.odMM-item(catalog,endNps).odMM)/2));
   center=mul(add(start,end),.5);
  }else if(c.kind==='flange'){
   length=flange.lengthMM;end=add(start,mul(axis,length));center=mul(add(start,end),.5);endType=reverse?'plain':'flanged';
  }else if(c.kind==='valve'){
   length=Math.max(c.lengthMM,flange.lengthMM*2+pipe.odMM*1.3);end=add(start,mul(axis,length));center=mul(add(start,end),.5);endType='flanged';
  }else if(c.kind==='cap'){
   length=flange.thicknessMM;end=add(start,mul(axis,length));center=mul(add(start,end),.5);endType='closed';
  }
  const node={...c,nps,rating,start,end,axis,endAxis,normal:n,center,length,flange,odMM:pipe.odMM,endNps,endType,branch,adapter,reverse,origin};nodes.push(node);used.add(c.parentPort);
  if(c.kind!=='cap')ports.set(c.id+':out',{id:c.id+':out',position:end,axis:endAxis,nps:endNps,endType,rating,label:c.tag+' · salida'});
  if(branch)ports.set(branch.id,branch);
 }
 const freePorts=[...ports.values()].filter(p=>!used.has(p.id));return {nodes,ports,freePorts};
}
export function descendants(d,id){const ids=new Set([id]);let change=true;while(change){change=false;for(const c of d.components)if(ids.has(c.parentPort.split(':')[0])&&!ids.has(c.id)){ids.add(c.id);change=true;}}return ids;}
export function materialRows(result,catalog){
 const rows=new Map();function push(kind,nps,rating,outNps=0,length=0,detail=''){
  const label=TYPES[kind]+(kind==='elbow'?' '+detail+'°':kind==='valve'?' '+(detail==='ball'?'bola':'compuerta'):kind==='reducer'?' '+(detail==='eccentric'?'excéntrico':'concéntrico'):''),measure=item(catalog,nps).label+(outNps?' × '+item(catalog,outNps).label:'');
  const cls=['flange','valve','cap'].includes(kind)?rating:'—',key=[label,measure,cls].join('|');if(!rows.has(key))rows.set(key,{description:label,nps:measure,rating:cls,quantity:0,lengthMM:0});const row=rows.get(key);row.quantity++;if(kind==='pipe')row.lengthMM+=length;
 }
 for(const n of result.nodes){if(n.adapter)push('flange',n.nps,n.rating);push(n.kind,n.nps,n.rating,n.kind==='reducer'?n.outNps:n.kind==='tee'&&n.branchNps!==n.nps?n.branchNps:0,n.length,n.kind==='elbow'?n.bendAngle:n.kind==='valve'?n.valveType:n.reduction);}
 return [...rows.values()];
}
