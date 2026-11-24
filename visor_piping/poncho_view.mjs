import * as THREE from 'three';
import {ponchoMesh} from './poncho.mjs';
import {pipeFrame} from './pipe_path.mjs';
import {add,mul,cross} from './model.mjs';
const v=a=>new THREE.Vector3(...a);
export function drawPoncho(node,parent,plateMaterial,weldMaterial){
 const p=node.pad,data=ponchoMesh(node),geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(data.positions,3));geometry.setIndex(data.indices);geometry.computeVertexNormals();const plate=new THREE.Mesh(geometry,plateMaterial);plate.name='Poncho de refuerzo · placa curva perforada';parent.add(plate);
 function seam(points,name){const mesh=new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points.map(v)),192,Math.max(1.8,p.thickness*.3),8,false),weldMaterial);mesh.name=name;parent.add(mesh);}
 seam(data.outer,'Soldadura perimetral del poncho');
 const host=node.origin.pipeNode,base=pipeFrame(host,node.tapOffsetMM),roll=node.rollDeg*Math.PI/180,radial=add(mul(base.normal,Math.cos(roll)),mul(base.binormal,Math.sin(roll))),side=cross(base.axis,radial),segments=64,layers=8,ring=segments+1,layer=(layers+1)*ring,positions=[],indices=[],radius=p.mainOD/2;
 function foot(r,angle,R){const x=r*Math.cos(angle),y=r*Math.sin(angle),f=pipeFrame(host,node.tapOffsetMM+x),theta=Math.asin(Math.max(-1,Math.min(1,y/R)));return add(f.point,add(mul(f.normal,R*Math.cos(roll+theta)),mul(f.binormal,R*Math.sin(roll+theta))));}
 for(const r of [p.branchOD/2,p.branchOD*.43])for(let j=0;j<=layers;j++)for(let i=0;i<=segments;i++){const a=i*2*Math.PI/segments,start=foot(r,a,radius),end=add(node.end,add(mul(base.axis,r*Math.cos(a)),mul(side,r*Math.sin(a))));positions.push(...add(mul(start,1-j/layers),mul(end,j/layers)));}
 for(let wall=0;wall<2;wall++)for(let j=0;j<layers;j++)for(let i=0;i<segments;i++){const a=wall*layer+j*ring+i,b=a+ring;indices.push(a,a+1,b,a+1,b+1,b);}
 for(const j of [0,layers])for(let i=0;i<segments;i++){const a=j*ring+i,b=layer+a;indices.push(a,b,a+1,a+1,b,b+1);}
 const neckGeometry=new THREE.BufferGeometry();neckGeometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));neckGeometry.setIndex(indices);neckGeometry.computeVertexNormals();const neck=new THREE.Mesh(neckGeometry,plateMaterial);neck.name='Ramal soldado al poncho';parent.add(neck);
 seam(Array.from({length:97},(_,i)=>foot(p.branchOD/2,i*Math.PI*2/96,radius+.5+p.thickness)),'Soldadura de ramal a poncho');
}
