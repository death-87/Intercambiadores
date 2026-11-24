import * as THREE from 'three';
import {stairLayout} from './external.mjs';

function box(group,material,size,position){
 const mesh=new THREE.Mesh(new THREE.BoxGeometry(...size),material);
 mesh.position.set(...position);
 group.add(mesh);
 return mesh;
}

function rail(group,material,a,b,radius){
 const start=new THREE.Vector3(...a),end=new THREE.Vector3(...b);
 const direction=end.clone().sub(start);
 const mesh=new THREE.Mesh(new THREE.CylinderGeometry(radius,radius,direction.length(),8),material);
 mesh.position.copy(start).lerp(end,.5);
 mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),direction.normalize());
 group.add(mesh);
}

export function drawExternalObject(parent,object,selected){
 const group=new THREE.Group();
 group.userData.externalId=object.id;
 group.position.set(...object.position);
 group.rotation.set(...object.rotation.map(deg=>deg*Math.PI/180),'XYZ');
 parent.add(group);
 const {a,b,height}=object;
 const surface=new THREE.MeshStandardMaterial({
  color:selected?0x168b78:object.kind==='support'?0xa8a49b:0x8398a4,
  roughness:object.kind==='support'?.92:.48,
  metalness:object.kind==='support'?0:.42,
 });
 if(object.kind==='support'){
  box(group,surface,[a,b,height],[0,0,height/2]);
  return;
 }
 const stair=new THREE.MeshStandardMaterial({color:0x43535d,metalness:.55,roughness:.45});
 const shell=new THREE.Mesh(new THREE.CylinderGeometry(a/2,a/2,height,64),surface);
 shell.rotation.x=Math.PI/2;
 shell.position.z=height/2;
 group.add(shell);
 const {radius,steps,sweep}=stairLayout(a,b,height);
 const rise=height/steps,depth=2*radius*Math.sin(sweep/(2*steps))*1.08;
 const railHeight=Math.min(1100,Math.max(100,height*.35)),railRadius=Math.min(28,b*.045);
 const point=(step,r,offset=0)=>{
  const angle=sweep*step/steps;
  return [r*Math.cos(angle),r*Math.sin(angle),step*rise+offset];
 };
 for(let step=1;step<=steps;step++){
  const tread=box(group,stair,[b,depth,Math.min(65,rise*.32)],point(step,radius,-Math.min(65,rise*.32)/2));
  tread.rotation.z=sweep*step/steps;
 }
 for(const radiusEdge of [radius-b*.45,radius+b*.45]){
  // Smooth enough for the cylindrical profile, with posts spaced along the stair.
  const segments=Math.min(48,steps),postEvery=Math.max(1,Math.floor(segments/10));
  for(let index=0;index<=segments;index++){
   const step=index*steps/segments;
   if(index%postEvery===0||index===segments)
    rail(group,stair,point(step,radiusEdge),point(step,radiusEdge,railHeight),railRadius);
   if(index)
    rail(group,stair,point((index-1)*steps/segments,radiusEdge,railHeight),point(step,radiusEdge,railHeight),railRadius);
  }
 }
}
