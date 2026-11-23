// Asiento del elbolet sobre la superficie curva real del codo, en mm.
const add=(a,b)=>a.map((x,i)=>x+b[i]),sub=(a,b)=>a.map((x,i)=>x-b[i]),mul=(a,s)=>a.map(x=>x*s),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
export function elbowDistance(point,host){
 const q=sub(point,host.start),R=host.radiusMM,t=Math.max(0,Math.min(host.angleRad,Math.atan2(dot(q,host.axis),R-dot(q,host.normal))));
 const center=add(host.start,add(mul(host.axis,R*Math.sin(t)),mul(host.normal,R*(1-Math.cos(t)))));return Math.hypot(...sub(point,center));
}
export function elbowSeat(origin,direction,host){
 const radius=host.odMM/2,step=Math.max(1,radius/8),limit=host.radiusMM*4+host.odMM*8;
 let low=0,high=step;if(elbowDistance(origin,host)>radius+.01)throw Error('La base del elbolet no intersecta el codo.');
 while(high<limit&&elbowDistance(add(origin,mul(direction,high)),host)<=radius){low=high;high+=step;}
 if(high>=limit)throw Error('No se encontró el asiento del elbolet sobre el codo.');
 for(let i=0;i<36;i++){const mid=(low+high)/2;if(elbowDistance(add(origin,mul(direction,mid)),host)<=radius)low=mid;else high=mid;}
 return (low+high)/2;
}
