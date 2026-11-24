import * as THREE from 'three';
import {add,sub,mul,norm,normal,cross} from './model.mjs';
import {annotationPoint} from './details.mjs';
const v=a=>new THREE.Vector3(...a),zaxis=new THREE.Vector3(0,0,1);
export function drawRepairs(parent,design,result,repairMaterial,weldMaterial){
 for(const repair of design.repairs||[]){const node=result.nodes.find(n=>n.id===repair.hostId),axis=node.axis,u=normal(axis,repair.rollDeg),b=cross(axis,u),start=add(node.start,mul(axis,repair.startMM)),r=node.odMM/2+1,R=r+repair.thicknessMM,angle=repair.type==='type_b'?Math.PI*2:repair.coverageDeg*Math.PI/180,begin=-angle/2,group=new THREE.Group();group.userData={repairId:repair.id,componentId:node.id};group.name=repair.tag+' · '+repair.type;parent.add(group);
  const shape=new THREE.Shape();shape.absarc(0,0,R,begin,begin+angle,false);if(repair.type==='type_b'){shape.closePath();const hole=new THREE.Path();hole.absarc(0,0,r,0,Math.PI*2,true);shape.holes.push(hole);}else{shape.lineTo(Math.cos(begin+angle)*r,Math.sin(begin+angle)*r);shape.absarc(0,0,r,begin+angle,begin,true);shape.closePath();}
  const body=new THREE.Mesh(new THREE.ExtrudeGeometry(shape,{depth:repair.lengthMM,bevelEnabled:false,curveSegments:64}),repairMaterial);body.name=repair.type==='type_b'?'Camisa Tipo B soldada':'Parche curvo soldado';body.position.copy(v(start));body.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(v(u),v(b),v(axis)));group.add(body);
  function point(t,x){return add(add(start,mul(axis,x)),add(mul(u,Math.cos(t)*R),mul(b,Math.sin(t)*R)));}
  function seam(points,name){const curve=new THREE.CatmullRomCurve3(points.map(v)),weld=new THREE.Mesh(new THREE.TubeGeometry(curve,Math.max(8,points.length*2),Math.max(1.5,repair.thicknessMM*.25),8,false),weldMaterial);weld.name=name;group.add(weld);}
  for(const x of [0,repair.lengthMM])seam(Array.from({length:65},(_,i)=>point(begin+angle*i/64,x)),'Soldadura de extremo de reparación');
  for(const t of repair.type==='type_b'?[begin,begin+Math.PI]:[begin,begin+angle])seam([point(t,0),point(t,repair.lengthMM)],'Soldadura longitudinal de reparación');
 }
}
function bubbleTexture(annotation){
 const canvas=document.createElement('canvas');canvas.width=900;canvas.height=224;const ctx=canvas.getContext('2d');ctx.fillStyle='#ffffff';if(annotation.style!=='arrow'){ctx.beginPath();ctx.arc(95,112,65,0,Math.PI*2);ctx.fill();ctx.strokeStyle=annotation.color;ctx.lineWidth=6;ctx.stroke();}
 ctx.fillStyle=annotation.color;ctx.textAlign='center';let font=50;do{ctx.font='bold '+font+'px sans-serif';font-=2;}while(ctx.measureText(annotation.number).width>112&&font>12);ctx.fillText(annotation.number,95,129,112);
 ctx.textAlign='left';ctx.font='42px sans-serif';const words=annotation.text.split(/\s+/),lines=[];let line='';for(const word of words){const next=line?line+' '+word:word;if(ctx.measureText(next).width>660&&line){lines.push(line);line=word;}else line=next;}if(line)lines.push(line);for(let i=0;i<Math.min(3,lines.length);i++)ctx.fillText(lines[i]+(i===2&&lines.length>3?'…':''),190,65+i*52,670);
 const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;return texture;
}
export function createAnnotations(parent,design){
 for(const annotation of design.annotations||[]){const group=new THREE.Group();group.userData.annotationId=annotation.id;parent.add(group);
  const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:bubbleTexture(annotation),transparent:true,depthTest:false,depthWrite:false}));sprite.center.set(95/900,.5);sprite.renderOrder=100;group.add(sprite);group._bubble=sprite;
  if(annotation.style!=='circle'){const arrow=new THREE.ArrowHelper(new THREE.Vector3(0,1,0),new THREE.Vector3(),1,annotation.color,1,.5);arrow.line.geometry=arrow.line.geometry.clone();arrow.cone.geometry=arrow.cone.geometry.clone();arrow.traverse(o=>{if(o.material){o.material.depthTest=false;o.material.depthWrite=false;}o.renderOrder=99;});group.add(arrow);group._arrow=arrow;}
 }
}
export function arrangeAnnotations(parent,design,result,camera,renderer,capturing=false){
 if(!parent.children.length)return;camera.updateMatrixWorld();const size=renderer.getSize(new THREE.Vector2()),units=(camera.top-camera.bottom)/camera.zoom/size.y,scale=capturing?1.35:1;
 for(const group of parent.children){const annotation=design.annotations.find(a=>a.id===group.userData.annotationId);if(!annotation)continue;const point=annotationPoint(annotation,result,design),projected=v(point).project(camera);let x=(projected.x+1)*size.x/2+(annotation.style==='circle'?0:annotation.offsetX*scale),y=(1-projected.y)*size.y/2+(annotation.style==='circle'?0:annotation.offsetY*scale);
  x=Math.max(35*scale,Math.min(size.x-245*scale,x));y=Math.max(45*scale,Math.min(size.y-45*scale,y));const label=new THREE.Vector3(x/size.x*2-1,1-y/size.y*2,projected.z).unproject(camera);group._bubble.position.copy(label);group._bubble.scale.set(units*900*scale*.30,units*224*scale*.30,1);
  if(group._arrow){const delta=v(point).sub(label),length=delta.length();group._arrow.visible=length>units*18;group._arrow.position.copy(label);group._arrow.setDirection(delta.normalize());group._arrow.setLength(length,Math.min(length*.25,units*13*scale),units*8*scale);}
 }
}
