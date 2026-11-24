import {pipeFrame} from './pipe_path.mjs';

export const EXTERNAL_TYPES={support:'Soporte de concreto',tank:'Estanque de almacenamiento'};

export function validateExternalObjects(objects=[]){
 if(!Array.isArray(objects)||objects.length>30)throw Error('Se admiten hasta 30 elementos externos.');
 const ids=new Set();
 for(const object of objects){
  if(!object||typeof object.id!=='string'||!/^[a-zA-Z0-9_-]{1,64}$/.test(object.id)||ids.has(object.id)||
   !Object.hasOwn(EXTERNAL_TYPES,object.kind)||typeof object.tag!=='string'||!object.tag.trim()||object.tag.length>60)
   throw Error('Identificación de elemento externo inválida.');
  ids.add(object.id);
  for(const [key,limit] of [['position',10000000],['rotation',360]]){
   const values=object[key];
   if(!Array.isArray(values)||values.length!==3||values.some(value=>!Number.isFinite(value)||Math.abs(value)>limit))
    throw Error('Posición o rotación de elemento externo inválida.');
  }
  if([object.a,object.b,object.height].some(value=>!Number.isFinite(value)||value<10||value>100000))
   throw Error('Las dimensiones del elemento externo deben estar entre 10 y 100.000 mm.');
 }
}

export function supportPosition(pipe,fraction,height,rotation){
 if(!pipe||pipe.kind!=='pipe'||!Number.isFinite(fraction)||fraction<0||fraction>1)
  throw Error('Selecciona un tramo y una ubicación entre 0 y 100%.');
 const {point,axis}=pipeFrame(pipe,pipe.length*fraction);
 const radial=[axis[0]*axis[2],axis[1]*axis[2],axis[2]**2-1];
 const norm=Math.hypot(...radial);
 if(norm<0.05)throw Error('Elige un punto donde el tramo no sea vertical.');
 const [x,y]=rotation.map(deg=>deg*Math.PI/180);
 // Dirección del eje Z local tras aplicar la rotación XYZ de Three.js.
 const top=[Math.sin(y),-Math.sin(x)*Math.cos(y),Math.cos(x)*Math.cos(y)];
 if(top[2]<=0)throw Error('Orienta la cara superior del soporte hacia la tubería.');
 return point.map((value,i)=>Math.round((value+radial[i]*pipe.odMM/(2*norm)-height*top[i])*100)/100);
}

export function stairLayout(diameter,width,height){
 const radius=diameter/2+width/2;
 const steps=Math.max(2,Math.min(300,Math.ceil(height/200)));
 const sweep=Math.min(1.75*Math.PI,Math.max(Math.PI/9,height*1.35/radius));
 return {radius,steps,sweep};
}
