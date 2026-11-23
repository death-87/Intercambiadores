import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {add,sub,mul,norm,normal,cross,blankDesign,compute,validateDesign,descendants,item,materialRows,TYPES} from './model.mjs';
const $=id=>document.getElementById(id),catalog=await fetch('./catalogo.json').then(r=>r.json());
const uid=()=>((globalThis.crypto?.randomUUID?.()||Date.now().toString(36)+Math.random().toString(36).slice(2)).replaceAll('-',''));
const STORAGE='jndigital.piping.design.v1';let design=blankDesign(),result=compute(design,catalog),selected=null,activePort='origin',undo=[],redo=[],loaded=false,loadToken=null,timer=null,labelsVisible=true,serverArgs={},storageWarning='';
const send=(type,data={})=>window.parent.postMessage({isStreamlitMessage:true,type,...data},'*');
function height(){send('streamlit:setFrameHeight',{height:Math.max(880,document.body.scrollHeight+8)});}
function status(text,error=false){$('status').textContent=text+(storageWarning&&!error?' · '+storageWarning:'');$('status').classList.toggle('error',error||!!storageWarning);}
function notify(action='update',extra={}){clearTimeout(timer);const transmit=()=>send('streamlit:setComponentValue',{value:{action,token:loadToken,design:structuredClone(design),materials:materialRows(result,catalog),...extra},dataType:'json'});if(action==='update')timer=setTimeout(transmit,350);else transmit();}
function persist(){design.updatedAt=new Date().toISOString();try{localStorage.setItem(STORAGE,JSON.stringify(design));storageWarning='';}catch{storageWarning='El respaldo local no está disponible. Descarga el JSON para conservar el diseño.';status(storageWarning,true);}notify();}
function setDesign(next,record=true){validateDesign(next,catalog);const layout=compute(next,catalog);if(record){undo.push(structuredClone(design));if(undo.length>30)undo.shift();redo=[];}design=next;result=layout;selected=design.components.some(c=>c.id===selected)?selected:null;if(!result.freePorts.some(p=>p.id===activePort))activePort=result.freePorts.at(-1)?.id||'';refresh();persist();renderModel();}
function mutate(fn){try{const next=structuredClone(design);fn(next);setDesign(next);return true;}catch(e){status(e.message,true);return false;}}
function exportFile(name,content,mime){const url=URL.createObjectURL(new Blob([content],{type:mime})),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function filename(){return (design.title||'Piping').replace(/[^\p{L}\p{N}_.-]+/gu,'_').slice(0,100);}
function nextTag(kind){const prefix={pipe:'P',elbow:'C',tee:'T',reducer:'R',valve:'V',flange:'F',cap:'BC'}[kind];let n=1;while(design.components.some(c=>c.tag===prefix+String(n).padStart(2,'0')))n++;return prefix+String(n).padStart(2,'0');}
for(const id of ['nps','out-nps'])for(const row of catalog.items)$(id).add(new Option(row.label,row.nps));
function context(){return selected?result.nodes.find(n=>n.id===selected)?.origin:result.ports.get(activePort);}
function defaults(){const kind=$('kind').value,p=context(),nps=p?.nps||Number($('nps').value)||2,od=item(catalog,nps).odMM;$('nps').value=nps;$('tag').value=nextTag(kind);$('out-nps').value=nps;$('length').value=kind==='pipe'?1000:kind==='valve'?Math.max(300,od*6):Math.max(100,od*3);$('radius').value=(nps*25.4*1.5).toFixed(2);$('branch-length').value=Math.max(75,od*1.5).toFixed(1);$('roll').value=0;conditional();}
function conditional(){const kind=$('kind').value,p=context(),nps=p?.nps??Number($('nps').value);$('nps').disabled=p?.nps!==null&&p?.nps!==undefined;if(p?.nps)$('nps').value=p.nps;
 $('rating').disabled=p?.endType==='flanged';if(p?.endType==='flanged')$('rating').value=p.rating;
 for(const [id,on] of [['out-row',['reducer','tee'].includes(kind)],['length-row',!['elbow','flange','cap'].includes(kind)],['elbow-row',kind==='elbow'],['branch-row',kind==='tee'],['reducer-row',kind==='reducer'],['valve-row',kind==='valve']])$(id).hidden=!on;
 $('roll').disabled=['pipe','flange','cap'].includes(kind);
 for(const option of $('out-nps').options)option.disabled=kind==='tee'&&Number(option.value)>nps;
 if(kind==='tee'&&Number($('out-nps').value)>nps)$('out-nps').value=nps;
 const spec=item(catalog,nps),f=spec.flanges[$('rating').value];$('dim-info').textContent=`DE cañería: ${spec.odMM} mm · Brida ${$('rating').value}: Ø ${f.diameterMM.toFixed(1)} mm · espesor ${f.thicknessMM.toFixed(1)} mm · ${f.boltCount} pernos.`;
 $('apply').disabled=!selected;$('delete').disabled=!selected;$('add').disabled=!activePort;
}
function form(){const source=selected?design.components.find(c=>c.id===selected):null;return {id:source?.id||'c'+uid().slice(0,24),parentPort:source?.parentPort||activePort,kind:$('kind').value,tag:$('tag').value.trim()||nextTag($('kind').value),nps:Number($('nps').value),outNps:Number($('out-nps').value),branchNps:Number($('out-nps').value),rating:$('rating').value,lengthMM:Number($('length').value),radiusMM:Number($('radius').value),branchLengthMM:Number($('branch-length').value),rollDeg:Number($('roll').value),bendAngle:Number($('bend').value),reduction:$('reduction').value,valveType:$('valve-type').value};}
function refresh(){
 $('title').value=design.title;$('direction').value=design.direction;$('direction').disabled=design.components.length>0;$('count').textContent=design.components.length+' componentes';$('project').textContent=design.title;$('empty').hidden=design.components.length>0;
 $('port').replaceChildren(...result.freePorts.map(p=>new Option(p.label+(p.nps?' · '+item(catalog,p.nps).label:''),p.id)));$('port').value=activePort;
 const p=result.ports.get(activePort);$('port-info').textContent=p?`X ${p.position[0].toFixed(1)} · Y ${p.position[1].toFixed(1)} · Z ${p.position[2].toFixed(1)} mm${p.endType==='flanged'?' · Enflanchado '+p.rating:''}`:'No quedan extremos abiertos. Selecciona un elemento para modificarlo.';
 $('component-list').replaceChildren(...result.nodes.map(n=>new Option(n.tag+' · '+TYPES[n.kind]+' · '+item(catalog,n.nps).label,n.id)));$('component-list').value=selected||'';$('undo').disabled=!undo.length;$('redo').disabled=!redo.length;conditional();height();
}
function selectNode(id){selected=id;const c=design.components.find(c=>c.id===id);if(c){for(const [field,key] of [['kind','kind'],['tag','tag'],['nps','nps'],['rating','rating'],['length','lengthMM'],['radius','radiusMM'],['branch-length','branchLengthMM'],['roll','rollDeg'],['bend','bendAngle'],['reduction','reduction'],['valve-type','valveType']])$(field).value=c[key];$('out-nps').value=c.kind==='tee'?c.branchNps:c.outNps;status('Seleccionado '+c.tag+'. Modifica sus valores y pulsa Aplicar cambios.');}refresh();highlight();}
const wrap=$('viewport'),scene=new THREE.Scene();scene.background=new THREE.Color('#edf3f7');
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));wrap.append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-1000,1000,700,-700,.1,1e7);camera.up.set(0,0,1);camera.position.set(3000,-3000,3000);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.08;controls.zoomSpeed=.7;controls.panSpeed=.7;controls.minZoom=.02;controls.maxZoom=80;
scene.add(new THREE.HemisphereLight(0xffffff,0x6a8193,2.4));const sun=new THREE.DirectionalLight(0xffffff,2.5);sun.position.set(3,-4,6);scene.add(sun);
const model=new THREE.Group(),portsGroup=new THREE.Group(),labelsGroup=new THREE.Group();scene.add(model,portsGroup,labelsGroup);
const grid=new THREE.GridHelper(10000,50,0xc9d8e2,0xdfE8ee);grid.rotation.x=Math.PI/2;grid.position.z=-1;scene.add(grid);
const axes=new THREE.AxesHelper(300);scene.add(axes);
const metal=new THREE.MeshStandardMaterial({color:0x7895a7,metalness:.6,roughness:.36,side:THREE.DoubleSide}),flangeMat=new THREE.MeshStandardMaterial({color:0xa7b9c5,metalness:.65,roughness:.3}),valveMat=new THREE.MeshStandardMaterial({color:0x168b78,metalness:.4,roughness:.37}),innerMat=new THREE.MeshStandardMaterial({color:0x415d70,roughness:.8,side:THREE.DoubleSide}),nutMat=new THREE.MeshStandardMaterial({color:0x445b6b,metalness:.65,roughness:.4});
function planeQuaternion(axis){const n=normal(axis),b=cross(axis,n);return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(new THREE.Vector3(...n),new THREE.Vector3(...b),new THREE.Vector3(...axis)));}
const v=a=>new THREE.Vector3(...a),yaxis=new THREE.Vector3(0,1,0),zaxis=new THREE.Vector3(0,0,1),shared=new Set([metal,flangeMat,valveMat,innerMat,nutMat]);
function clear(group){while(group.children.length){const c=group.children[0];group.remove(c);c.traverse(o=>{o.geometry?.dispose();if(o.material){for(const m of Array.isArray(o.material)?o.material:[o.material])if(!shared.has(m)){m.map?.dispose();m.dispose();}}});}}
function mesh(geo,mat,parent=model){const m=new THREE.Mesh(geo,mat);parent.add(m);return m;}
function cylinder(a,b,r,mat=metal,parent=model,r2=r){const delta=v(sub(b,a)),m=mesh(new THREE.CylinderGeometry(r2,r,delta.length(),32,1,false),mat,parent);m.position.copy(v(mul(add(a,b),.5)));m.quaternion.setFromUnitVectors(yaxis,delta.normalize());return m;}
function tube(a,b,od,parent,mat=metal){const axis=norm(sub(b,a)),len=Math.hypot(...sub(b,a)),r=od/2,inside=r*.86;
 for(const [radius,material] of [[r,mat],[inside,innerMat]]){const m=mesh(new THREE.CylinderGeometry(radius,radius,len,36,1,true),material,parent);m.position.copy(v(mul(add(a,b),.5)));m.quaternion.setFromUnitVectors(yaxis,v(axis));}
 for(const p of [a,b]){const m=mesh(new THREE.RingGeometry(inside,r,36),mat,parent);m.position.copy(v(p));m.quaternion.setFromUnitVectors(zaxis,v(axis));}
}
function plate(point,axis,f,parent,blind=false){const shape=new THREE.Shape();shape.absarc(0,0,f.diameterMM/2,0,Math.PI*2,false);
 if(!blind){const bore=new THREE.Path();bore.absarc(0,0,f.odMM*.43,0,Math.PI*2,true);shape.holes.push(bore);}
 for(let i=0;i<f.boltCount;i++){const a=(i+.5)*Math.PI*2/f.boltCount,hole=new THREE.Path();hole.absarc(Math.cos(a)*f.pitchMM/2,Math.sin(a)*f.pitchMM/2,f.holeMM/2,0,Math.PI*2,true);shape.holes.push(hole);}
 const m=mesh(new THREE.ExtrudeGeometry(shape,{depth:f.thicknessMM,bevelEnabled:false,curveSegments:48}),flangeMat,parent);m.name=blind?'Brida ciega':'Brida WN';m.userData.catalog={...f};m.position.copy(v(point));m.quaternion.copy(planeQuaternion(axis));return m;
}
function drawFlange(start,axis,f,parent){const rf=f.raisedFaceMM? (f.rating==='600#'?6.35:1.5875):0,hub=Math.max(1,f.lengthMM-f.thicknessMM-rf);
 cylinder(start,add(start,mul(axis,hub)),f.odMM/2,metal,parent,f.hubDiameterMM/2);plate(add(start,mul(axis,hub)),axis,f,parent);
 if(rf){const shape=new THREE.Shape();shape.absarc(0,0,f.raisedFaceMM/2,0,Math.PI*2,false);const hole=new THREE.Path();hole.absarc(0,0,f.odMM*.43,0,Math.PI*2,true);shape.holes.push(hole);const m=mesh(new THREE.ExtrudeGeometry(shape,{depth:rf,bevelEnabled:false,curveSegments:48}),flangeMat,parent);m.position.copy(v(add(start,mul(axis,f.lengthMM-rf))));m.quaternion.copy(planeQuaternion(axis));}
}
function bolts(seat,axis,f,parent){const n=normal(axis),b=cross(axis,n),nutH=Math.max(5,f.holeMM*.7),length=2*f.thicknessMM+3+nutH*3;
 for(let i=0;i<f.boltCount;i++){const a=(i+.5)*2*Math.PI/f.boltCount,rad=add(mul(n,Math.cos(a)*f.pitchMM/2),mul(b,Math.sin(a)*f.pitchMM/2)),p=add(seat,rad);
 const shaft=cylinder(add(p,mul(axis,-length/2)),add(p,mul(axis,length/2)),f.holeMM*.38,nutMat,parent);shaft.name='Espárrago de unión';
 for(const sign of [-1,1]){const nut=mesh(new THREE.CylinderGeometry(f.holeMM*.75,f.holeMM*.75,nutH,6),nutMat,parent);nut.name='Tuerca de unión';nut.position.copy(v(add(p,mul(axis,sign*(f.thicknessMM+nutH/2+1.5)))));nut.quaternion.setFromUnitVectors(yaxis,v(axis));}
 }
}
function reducer(n,parent){const r1=n.odMM/2,r2=item(catalog,n.outNps).odMM/2,normalA=normal(n.axis),normalB=cross(n.axis,normalA),verts=[],indices=[],steps=48;
 for(const [center,r] of [[n.start,r1],[n.end,r2]])for(let i=0;i<=steps;i++){const a=i*2*Math.PI/steps;verts.push(...add(center,add(mul(normalA,Math.cos(a)*r),mul(normalB,Math.sin(a)*r))));}
 for(let i=0;i<steps;i++){const a=i,b=i+1,c=i+steps+1,d=c+1;indices.push(a,b,c,b,d,c);}
 const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));geo.setIndex(indices);geo.computeVertexNormals();mesh(geo,metal,parent);
}
function label(text,position){const canvas=document.createElement('canvas');canvas.width=512;canvas.height=80;const ctx=canvas.getContext('2d');ctx.font='26px sans-serif';ctx.fillStyle='#1b3446';ctx.textAlign='center';const caption=text.slice(0,45);let fs=26;while(ctx.measureText(caption).width>480&&fs>13){fs--;ctx.font=fs+'px sans-serif';}ctx.fillText(caption,256,49,480);const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;const m=new THREE.SpriteMaterial({map:texture,depthTest:false,transparent:true});const sprite=new THREE.Sprite(m);sprite.position.copy(v(position));const scale=Math.max(250,totalSize*.23);sprite.scale.set(scale,scale*80/512,1);sprite.userData={anchor:[...position],textWidth:ctx.measureText(caption).width,fontSize:fs};labelsGroup.add(sprite);return sprite;}
let totalSize=1500,capturing=false;
function renderModel(){
 clear(model);clear(portsGroup);clear(labelsGroup);
 for(const n of result.nodes){const group=new THREE.Group();group.userData.id=n.id;model.add(group);const f={...n.flange,rating:n.rating};
  if(n.adapter)drawFlange(n.adapter.start,n.adapter.axis,f,group);
  if(n.origin.endType==='flanged'){bolts(add(n.origin.position,mul(n.axis,1.5)),n.axis,f,group);}else if(n.adapter&&!n.adapter.reverse){bolts(add(n.adapter.start,mul(n.axis,f.lengthMM+1.5)),n.axis,f,group);}
  if(n.kind==='pipe')tube(n.start,n.end,n.odMM,group);
  else if(n.kind==='elbow'){const R=Math.max(n.radiusMM,n.odMM*.6),angle=n.bendAngle*Math.PI/180,path=new THREE.Curve();path.getPoint=t=>v(add(n.start,add(mul(n.axis,R*Math.sin(angle*t)),mul(n.normal,R*(1-Math.cos(angle*t))))));mesh(new THREE.TubeGeometry(path,48,n.odMM/2,24,false),metal,group);}
  else if(n.kind==='tee'){tube(n.start,n.end,n.odMM,group);tube(n.center,n.branch.position,item(catalog,n.branchNps).odMM,group);}
  else if(n.kind==='reducer')reducer(n,group);
  else if(n.kind==='flange')drawFlange(n.reverse?n.end:n.start,n.reverse?mul(n.axis,-1):n.axis,f,group);
  else if(n.kind==='cap')plate(n.start,n.axis,f,group,true);
  else if(n.kind==='valve'){
   drawFlange(add(n.start,mul(n.axis,f.lengthMM)),mul(n.axis,-1),f,group);drawFlange(sub(n.end,mul(n.axis,f.lengthMM)),n.axis,f,group);
   tube(add(n.start,mul(n.axis,f.lengthMM)),sub(n.end,mul(n.axis,f.lengthMM)),n.odMM,group,valveMat);
   const body=mesh(n.valveType==='ball'?new THREE.SphereGeometry(n.odMM*.85,32,24):new THREE.BoxGeometry(n.odMM*1.8,n.odMM*1.4,n.odMM*1.8),valveMat,group);body.position.copy(v(n.center));body.quaternion.setFromUnitVectors(yaxis,v(n.axis));
   const stemStart=add(n.center,mul(n.normal,n.odMM*.6)),stemEnd=add(n.center,mul(n.normal,n.odMM*2.5));cylinder(stemStart,stemEnd,n.odMM*.09,nutMat,group);
   if(n.valveType==='gate'){const wheel=mesh(new THREE.TorusGeometry(n.odMM*.7,n.odMM*.07,10,40),valveMat,group);wheel.position.copy(v(stemEnd));wheel.quaternion.setFromUnitVectors(zaxis,v(n.normal));for(const a of [0,Math.PI/2]){const side=add(mul(n.axis,Math.cos(a)*n.odMM*.65),mul(cross(n.normal,n.axis),Math.sin(a)*n.odMM*.65));cylinder(sub(stemEnd,side),add(stemEnd,side),n.odMM*.04,valveMat,group);}}
   else cylinder(stemEnd,add(stemEnd,mul(n.axis,n.odMM*2)),n.odMM*.10,valveMat,group);
  }
 }
 const box=new THREE.Box3().setFromObject(model);totalSize=box.isEmpty()?1500:Math.max(box.getSize(new THREE.Vector3()).length(),500);
 for(const n of result.nodes){const shift=Math.max(n.odMM*(n.kind==='valve'?3.3:1.3),totalSize*.06),point=add(n.center,mul(n.normal,shift));const sprite=label(n.tag+(n.kind==='pipe'?' · '+n.length.toFixed(0)+' mm':''),point);const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints([v(n.center),v(point)]),new THREE.LineBasicMaterial({color:0x607e90,transparent:true,opacity:.8,depthTest:false}));sprite.userData.line=line;sprite.userData.center=[...n.center];labelsGroup.add(line);}
 for(const p of result.freePorts){const r=Math.max(8,Math.min(40,totalSize*.012)),m=mesh(new THREE.SphereGeometry(r,20,16),new THREE.MeshStandardMaterial({color:p.id===activePort?0xf7a73b:0x20b99d,emissive:p.id===activePort?0x422200:0x003329}),portsGroup);m.position.copy(v(p.position));m.userData.portId=p.id;}
 labelsGroup.visible=labelsVisible;grid.scale.setScalar(Math.max(1,totalSize/6000));axes.scale.setScalar(Math.max(1,totalSize/2000));highlight();fit('current');
}
function highlight(){model.traverse(o=>{if(o.isMesh&&o.material){const id=o.parent?.userData.id;/* Materiales compartidos se mantienen neutros; la selección usa un recuadro. */}});const old=scene.getObjectByName('selection-box');if(old){scene.remove(old);old.geometry.dispose();old.material.dispose();}if(selected){const group=model.children.find(g=>g.userData.id===selected);if(group){const box=new THREE.BoxHelper(group,0x0c9b87);box.name='selection-box';scene.add(box);}}}
function arrangeLabels(){
 if(!labelsVisible)return;
 camera.updateMatrixWorld();const size=renderer.getSize(new THREE.Vector2()),w=size.x,h=size.y,units=(camera.top-camera.bottom)/camera.zoom/h,font=capturing?22:13,occupied=[];
 for(const sprite of labelsGroup.children.filter(o=>o.isSprite)){
  const data=sprite.userData,projected=v(data.anchor).project(camera),labelWidth=Math.max(24,data.textWidth*font/data.fontSize),labelHeight=font+5;
  let x=(projected.x+1)*w/2,y=(1-projected.y)*h/2;x=Math.max(labelWidth/2+12,Math.min(w-labelWidth/2-12,x));y=Math.max(labelHeight+12,Math.min(h-labelHeight-15,y));
  for(let attempt=0;attempt<14;attempt++){const box={x:x-labelWidth/2-4,y:y-labelHeight/2-3,w:labelWidth+8,h:labelHeight+6};if(!occupied.some(r=>box.x<r.x+r.w&&box.x+box.w>r.x&&box.y<r.y+r.h&&box.y+box.h>r.y)){occupied.push(box);break;}y-=labelHeight+6;if(y<25){y=Math.min(h-30,(1-projected.y)*h/2+labelHeight*(attempt+1));x=Math.min(w-labelWidth/2-12,x+30);}}
  sprite.scale.set(units*512*font/data.fontSize,units*80*font/data.fontSize,1);sprite.position.set(x/w*2-1,1-y/h*2,projected.z).unproject(camera);
  if(data.line){const attr=data.line.geometry.getAttribute('position');attr.setXYZ(0,...data.center);attr.setXYZ(1,sprite.position.x,sprite.position.y,sprite.position.z);attr.needsUpdate=true;}
 }
}
function fit(view='iso',aspectOverride=null){
 const box=new THREE.Box3().setFromObject(model);if(box.isEmpty())box.setFromCenterAndSize(new THREE.Vector3(),new THREE.Vector3(1200,1200,800));
 const center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3()),extent=Math.max(size.length(),500),aspect=aspectOverride||((wrap.clientWidth||800)/(wrap.clientHeight||650));
 let direction={iso:[1,-1,1],front:[0,-1,0],top:[0,0,1],side:[1,0,0]}[view];if(!direction)direction=camera.position.clone().sub(controls.target).normalize().toArray();
 const damping=controls.enableDamping;controls.enableDamping=false;controls.update();controls.enableDamping=damping;
 controls.target.copy(center);camera.up.set(...(view==='top'?[0,1,0]:[0,0,1]));camera.position.copy(center).addScaledVector(v(direction).normalize(),extent*3);camera.lookAt(center);camera.updateMatrixWorld();
 let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;model.updateMatrixWorld(true);
 model.traverse(o=>{if(!o.isMesh||!o.geometry)return;if(!o.geometry.boundingBox)o.geometry.computeBoundingBox();const bounds=o.geometry.boundingBox,matrix=camera.matrixWorldInverse.clone().multiply(o.matrixWorld);for(const x of [bounds.min.x,bounds.max.x])for(const y of [bounds.min.y,bounds.max.y])for(const z of [bounds.min.z,bounds.max.z]){const p=new THREE.Vector3(x,y,z).applyMatrix4(matrix);minX=Math.min(minX,p.x);maxX=Math.max(maxX,p.x);minY=Math.min(minY,p.y);maxY=Math.max(maxY,p.y);}});
 let width,height;if(Number.isFinite(minX)){width=(maxX-minX)/2;height=(maxY-minY)/2;const shift=new THREE.Vector3((minX+maxX)/2,(minY+maxY)/2,0).applyQuaternion(camera.quaternion);camera.position.add(shift);controls.target.add(shift);camera.updateMatrixWorld();}else{width=600;height=400;}
 const h=Math.max(150,height,width/aspect)*1.38;camera.left=-h*aspect;camera.right=h*aspect;camera.top=h;camera.bottom=-h;camera.near=.1;camera.far=Math.max(1e6,extent*10);camera.zoom=1;camera.updateProjectionMatrix();controls.update();
}
function resize(){const w=wrap.clientWidth||800,h=wrap.clientHeight||650;renderer.setSize(w,h,false);fit('current');height();}
new ResizeObserver(resize).observe(wrap);$('panel').addEventListener('toggle',()=>{setTimeout(resize,50);height();});if(innerWidth<760)$('panel').open=false;
let down=null;renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;const rect=renderer.domElement.getBoundingClientRect(),mouse=new THREE.Vector2((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1),ray=new THREE.Raycaster();ray.setFromCamera(mouse,camera);const ports=ray.intersectObjects(portsGroup.children);if(ports.length){activePort=ports[0].object.userData.portId;selected=null;defaults();renderModel();refresh();status('Extremo seleccionado. El siguiente elemento se conectará aquí.');return;}const hits=ray.intersectObjects(model.children,true);if(hits.length){let node=hits[0].object;while(node&&!node.userData.id)node=node.parent;if(node)selectNode(node.userData.id);}});
async function capture(){
 const old={position:camera.position.clone(),target:controls.target.clone(),up:camera.up.clone(),left:camera.left,right:camera.right,top:camera.top,bottom:camera.bottom,zoom:camera.zoom,near:camera.near,far:camera.far,bg:scene.background},size=renderer.getSize(new THREE.Vector2()),pixel=renderer.getPixelRatio(),box=scene.getObjectByName('selection-box');
 capturing=true;controls.enabled=false;
 try{
  portsGroup.visible=false;grid.visible=false;axes.visible=false;if(box)box.visible=false;scene.background=new THREE.Color(0xffffff);renderer.setPixelRatio(1);renderer.setSize(1600,900,false);fit('iso',1600/900);arrangeLabels();renderer.render(scene,camera);return renderer.domElement.toDataURL('image/png');
 }finally{
  scene.background=old.bg;portsGroup.visible=true;grid.visible=true;axes.visible=true;if(box)box.visible=true;renderer.setPixelRatio(pixel);renderer.setSize(size.x,size.y,false);camera.position.copy(old.position);controls.target.copy(old.target);camera.up.copy(old.up);for(const key of ['left','right','top','bottom','zoom','near','far'])camera[key]=old[key];camera.updateProjectionMatrix();controls.enabled=true;controls.update();capturing=false;arrangeLabels();
 }
}
function guard(fn){return async()=>{try{await fn();}catch(e){status(e.message,true);}};}
$('add').onclick=guard(()=>{if(!activePort)throw Error('No hay un extremo libre.');const c=form();c.id='c'+uid().slice(0,24);c.parentPort=activePort;if(!mutate(d=>d.components.push(c)))return;selected=null;activePort=result.freePorts.find(p=>p.id===c.id+':out')?.id||result.freePorts.at(-1)?.id||'';defaults();renderModel();refresh();status('Elemento conectado. El respaldo local se actualizó.');});
$('apply').onclick=()=>{if(!selected)return;const c=form();if(mutate(d=>{d.components[d.components.findIndex(n=>n.id===selected)]=c;}))selectNode(selected);};
$('delete').onclick=()=>{if(!selected)return;const ids=descendants(design,selected);if(ids.size>1&&!confirm('Se eliminarán '+ids.size+' componentes, incluyendo las continuaciones. Puedes deshacerlo.'))return;mutate(d=>{d.components=d.components.filter(c=>!ids.has(c.id));});selected=null;defaults();refresh();};
$('clear').onclick=()=>{selected=null;defaults();refresh();highlight();};$('kind').onchange=defaults;$('nps').onchange=defaults;$('rating').onchange=conditional;$('port').onchange=()=>{activePort=$('port').value;selected=null;defaults();renderModel();refresh();};$('component-list').onchange=()=>selectNode($('component-list').value);
$('title').onchange=()=>mutate(d=>{d.title=$('title').value.trim()||'Línea de piping';});$('direction').onchange=()=>mutate(d=>{d.direction=$('direction').value;});
$('undo').onclick=()=>{if(!undo.length)return;redo.push(structuredClone(design));const d=undo.pop();selected=null;setDesign(d,false);defaults();};$('redo').onclick=()=>{if(!redo.length)return;undo.push(structuredClone(design));const d=redo.pop();selected=null;setDesign(d,false);defaults();};
$('save').onclick=()=>exportFile(filename()+'.json',JSON.stringify(design,null,2),'application/json');$('load').onclick=()=>$('file').click();$('file').onchange=guard(async()=>{const f=$('file').files[0];if(!f)return;if(f.size>2e6)throw Error('El JSON supera 2 MB.');setDesign(JSON.parse(await f.text()));selected=null;defaults();refresh();status('Diseño importado.');$('file').value='';});
$('example').onclick=guard(async()=>{if(design.components.length&&!confirm('¿Abrir el ejemplo? Podrás recuperar el diseño actual con Deshacer.'))return;selected=null;setDesign(await fetch('./ejemplo.json').then(r=>r.json()));activePort=result.freePorts.at(-1)?.id||'';defaults();refresh();fit('iso');status('Ejemplo cargado. Selecciona un elemento para editarlo o continúa desde un extremo.');});
$('new').onclick=()=>{if(design.components.length&&!confirm('¿Comenzar una línea nueva? Descarga antes el JSON si deseas conservar la actual.'))return;selected=null;activePort='origin';setDesign(blankDesign('p'+uid()));defaults();refresh();};
for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>fit(b.dataset.view==='fit'?'current':b.dataset.view);
$('labels').onclick=()=>{labelsVisible=!labelsVisible;labelsGroup.visible=labelsVisible;$('labels').textContent=labelsVisible?'Ocultar TAG':'Mostrar TAG';};
$('png').onclick=guard(async()=>{const data=await capture();const a=document.createElement('a');a.href=data;a.download=filename()+'.png';a.click();});
$('pdf').onclick=guard(async()=>{if(!design.components.length)throw Error('Agrega componentes antes de exportar.');status('Preparando isométrico y materiales…');notify('export_pdf',{image:await capture()});status('Captura lista. Descarga el PDF debajo del editor.');});
window.addEventListener('message',e=>{if(e.data.type!=='streamlit:render')return;serverArgs=e.data.args||{};if(loaded&&loadToken===serverArgs.load_token)return;loadToken=serverArgs.load_token;loaded=true;
 try{let initial=serverArgs.initial_data||blankDesign();if(!serverArgs.imported){try{const saved=JSON.parse(localStorage.getItem(STORAGE));if(saved?.version===1&&(!initial.components.length||saved.updatedAt>initial.updatedAt))initial=saved;}catch{}}
 validateDesign(initial,catalog);design=structuredClone(initial);result=compute(design,catalog);activePort=result.freePorts.at(-1)?.id||'';selected=null;renderModel();refresh();$('nps').value=2;defaults();notify();status('Diseño listo. El respaldo automático se conserva en este navegador.');
 }catch(err){status(err.message,true);}
});
function animate(){requestAnimationFrame(animate);controls.update();arrangeLabels();renderer.render(scene,camera);}animate();renderModel();refresh();$('nps').value=2;defaults();send('streamlit:componentReady',{apiVersion:1});height();
// Inspección de geometría sin datos privados para pruebas y soporte.
window.pipingEditor={getDesign:()=>structuredClone(design),getResult:()=>result,load:d=>setDesign(d),capture,scene,camera,model,renderer};
