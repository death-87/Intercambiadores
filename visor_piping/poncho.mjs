import {pipeFrame} from './pipe_path.mjs';
const add=(a,b)=>a.map((x,i)=>x+b[i]),mul=(a,k)=>a.map(x=>x*k);
export function ponchoDimensions(c,mainOD,branchOD,runLength){
 const length=c.padLengthMM??Math.max(250,branchOD*2),thickness=c.padThicknessMM??6,coverage=c.padCoverageDeg??160;
 for(const [name,value,min,max] of [['largo',length,20,10000],['espesor',thickness,.5,100],['cobertura',coverage,10,170]])if(typeof value!=='number'||!Number.isFinite(value)||value<min||value>max)throw Error('Dimensión de poncho inválida: '+name);
 if(c.lengthMM<=thickness+2)throw Error('La altura del ramal debe superar el espesor del poncho.');
 if(length/2<=branchOD/2+2||mainOD/2*Math.sin(coverage*Math.PI/360)<=branchOD/2+2)throw Error('Amplía el largo o la cobertura del poncho para rodear el ramal.');
 if(c.tapOffsetMM-length/2<-.001||c.tapOffsetMM+length/2>runLength+.001)throw Error('El poncho completo debe quedar dentro del tramo principal.');
 return {length,thickness,coverage,mainOD,branchOD};
}
export function ponchoMesh(node){
 const p=node.pad,host=node.origin.pipeNode,R=p.mainOD/2+.5,half=p.coverage*Math.PI/360,roll=node.rollDeg*Math.PI/180,steps=96,rings=12,positions=[],indices=[],hole=p.branchOD/2+.8;
 function sample(phi,q,radius){const x=p.length/2*Math.cos(phi)*q,theta=half*Math.sin(phi)*q,f=pipeFrame(host,node.tapOffsetMM+x);return add(f.point,add(mul(f.normal,radius*Math.cos(roll+theta)),mul(f.binormal,radius*Math.sin(roll+theta))));}
 function inner(phi,radius){let lo=0,hi=1;for(let i=0;i<40;i++){const q=(lo+hi)/2,x=p.length/2*Math.cos(phi)*q,y=radius*Math.sin(half*Math.sin(phi)*q);if(x*x+y*y<hole*hole)lo=q;else hi=q;}return (lo+hi)/2;}
 const layer=(rings+1)*(steps+1);
 for(const radius of [R,R+p.thickness])for(let j=0;j<=rings;j++)for(let i=0;i<=steps;i++){const phi=i*2*Math.PI/steps,q0=inner(phi,radius);positions.push(...sample(phi,q0+(1-q0)*j/rings,radius));}
 for(let side=0;side<2;side++)for(let j=0;j<rings;j++)for(let i=0;i<steps;i++){const a=side*layer+j*(steps+1)+i,b=a+steps+1;indices.push(a,a+1,b,a+1,b+1,b);}
 for(const j of [0,rings])for(let i=0;i<steps;i++){const a=j*(steps+1)+i,b=a+layer;indices.push(a,b,a+1,a+1,b,b+1);}
 const outer=Array.from({length:steps+1},(_,i)=>sample(i*2*Math.PI/steps,1,R+p.thickness));
 return {positions,indices,outer};
}
