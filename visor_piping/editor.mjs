import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {add,sub,mul,dot,norm,normal,cross,blankDesign,compute,validateDesign,descendants,item,materialRows,TYPES,VALVES,isRelief,isOlet} from './model.mjs';
import {elbowSeat} from './elbow_surface.mjs';
import {sortComponents} from './equipment.mjs';
import {loadAsset,validateAsset} from './assets.mjs';
const $=id=>document.getElementById(id),catalog=await fetch('./catalogo.json').then(r=>r.json());
const uid=()=>((globalThis.crypto?.randomUUID?.()||Date.now().toString(36)+Math.random().toString(36).slice(2)).replaceAll('-',''));
const STORAGE='jndigital.piping.design.v1';let design=blankDesign(),result=compute(design,catalog),selected=null,selectedEquipmentId=null,continuationId=null,activePort='origin',undo=[],redo=[],loaded=false,loadToken=null,timer=null,labelsVisible=true,serverArgs={},storageWarning='';
const send=(type,data={})=>window.parent.postMessage({isStreamlitMessage:true,type,...data},'*');
function height(){send('streamlit:setFrameHeight',{height:Math.max(880,document.body.scrollHeight+8)});}
function status(text,error=false){$('status').textContent=text+(storageWarning&&!error?' · '+storageWarning:'');$('status').classList.toggle('error',error||!!storageWarning);}
function notify(action='update',extra={}){clearTimeout(timer);const transmit=()=>send('streamlit:setComponentValue',{value:{action,token:loadToken,design:structuredClone(design),materials:materialRows(result,catalog),...extra},dataType:'json'});if(action==='update')timer=setTimeout(transmit,350);else transmit();}
let lastBackupAt=null,lastBackupFile='';function backupInfo(dirty=true){$('backup-info').textContent=dirty?(lastBackupAt?'Hay cambios posteriores a la última copia. ':'')+'Guarda el proyecto para descargar una copia completa de equipos y piping. En otro computador, usa Abrir proyecto guardado.':'Copia preparada el '+lastBackupAt+'. Archivo: '+lastBackupFile+'. Revisa Descargas y conserva el archivo JSON. Para continuar en otro computador, abre ese archivo; esta copia no se guarda en la nube.';}
function persist(){backupInfo();design.updatedAt=new Date().toISOString();try{localStorage.setItem(STORAGE,JSON.stringify(design));storageWarning='';}catch{storageWarning='El respaldo local no está disponible. Descarga el JSON para conservar el diseño.';status(storageWarning,true);}notify();}
function setDesign(next,record=true){validateDesign(next,catalog);for(const e of next.equipments||[])validateAsset(e.asset);const layout=compute(next,catalog);if(record){undo.push(structuredClone(design));if(undo.length>30)undo.shift();redo=[];}design=next;result=layout;selected=design.components.some(c=>c.id===selected)?selected:null;if(!result.freePorts.some(p=>p.id===activePort))activePort=result.freePorts.at(-1)?.id||'';refresh();persist();renderModel();}
function mutate(fn){try{const next=structuredClone(design);fn(next);setDesign(next);return true;}catch(e){status(e.message,true);return false;}}
function exportFile(name,content,mime){const url=URL.createObjectURL(new Blob([content],{type:mime})),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function filename(){return (design.title||'Piping').replace(/[^\p{L}\p{N}_.-]+/gu,'_').slice(0,100);}
function nextTag(kind){const prefix=kind==='valve'&&['psv','rv'].includes($('valve-type').value)?$('valve-type').value.toUpperCase():{pipe:'P',elbow:'C',tee:'T',sockolet:'SO',thredolet:'TH',latrolet:'LO',elbolet:'EO',reducer:'R',valve:'V',flange:'F',cap:'BC'}[kind];let n=1;while(design.components.some(c=>c.tag===prefix+String(n).padStart(2,'0')))n++;return prefix+String(n).padStart(2,'0');}
for(const id of ['nps','out-nps','tee-run-nps'])for(const row of catalog.items)$(id).add(new Option(row.label,row.nps));
function context(){if(['sockolet','thredolet','latrolet','elbolet'].includes($('kind').value))return result.ports.get($('run-pipe').value+':tap');return selected?result.nodes.find(n=>n.id===selected)?.origin:result.ports.get(activePort);}
function defaults(){const kind=$('kind').value;let host=result.nodes.find(n=>n.id===$('run-pipe').value);if(['sockolet','thredolet','latrolet','elbolet'].includes(kind)&&(host?.kind!==(kind==='elbolet'?'elbow':'pipe')||(kind==='elbolet'&&host.bendAngle!==90))){$('run-pipe').value=result.nodes.find(n=>n.kind===(kind==='elbolet'?'elbow':'pipe')&&(kind!=='elbolet'||n.bendAngle===90))?.id||'';}const p=context(),nps=p?.nps||Number($('nps').value)||2,od=item(catalog,nps).odMM;$('nps').value=nps;$('tag').value=nextTag(kind);$('out-nps').value=nps;$('length').value=kind==='pipe'?1000:kind==='valve'?Math.max(300,od*6):Math.max(100,od*3);$('radius').value=(nps*25.4*1.5).toFixed(2);$('branch-length').value=Math.max(75,od*1.5).toFixed(1);$('roll').value=0;$('tee-entry').value='a';$('tee-run-nps').value=nps;$('outlet-end').value='welded';$('branch-end').value='welded';$('inlet-end').value='auto';$('valve-connection').value=p?.endType==='threaded'?'threaded':'flanged';if(['sockolet','thredolet','latrolet','elbolet'].includes(kind)){const run=result.nodes.find(n=>n.id===$('run-pipe').value);if(run){$('tap-offset').value=run.length/2;$('tap-offset').max=run.length;$('length').value=100;}}conditional();refreshContinuation();}
function conditional(){const kind=$('kind').value,relief=kind==='valve'&&['psv','rv'].includes($('valve-type').value),p=context(),nps=p?.nps??Number($('nps').value);$('nps').disabled=p?.nps!==null&&p?.nps!==undefined;if(p?.nps)$('nps').value=p.nps;
 $('rating').disabled=p?.endType==='flanged'||kind==='valve'&&$('valve-connection').value==='threaded';if(p?.endType==='flanged')$('rating').value=p.rating;
 for(const [id,on] of [['tee-entry-row',kind==='tee'],['tee-run-row',kind==='tee'&&$('tee-entry').value==='branch'],['out-row',['reducer','tee','sockolet','thredolet','latrolet','elbolet'].includes(kind)||relief],['length-row',!['elbow','flange','cap'].includes(kind)],['elbow-row',kind==='elbow'],['branch-row',kind==='tee'||relief],['outlet-rating-row',relief&&$('valve-connection').value!=='threaded'],['sockolet-row',['sockolet','thredolet','latrolet','elbolet'].includes(kind)],['olet-angle-row',kind==='elbolet'],['elbolet-rotation-row',kind==='elbolet'&&$('olet-angle').value==='custom'],['ends-row',['pipe','elbow','tee','reducer'].includes(kind)],['branch-end-row',kind==='tee'],['reducer-row',kind==='reducer'],['valve-row',kind==='valve'],['pipe-inlet-row',kind==='pipe']])$(id).hidden=!on;
 $('length-row').querySelector('label').textContent=['sockolet','thredolet','latrolet','elbolet'].includes(kind)?'Altura de la derivación sobre la línea (mm)':relief?'Altura total PSV / RV (mm)':'Largo axial / entre caras (mm)';$('branch-row').querySelector('label').textContent=relief?'Largo de salida lateral al eje (mm)':'Largo al eje de derivación (mm)';
 $('tap-offset').disabled=kind==='elbolet';if(kind==='elbolet')$('tap-offset').value=0;for(const option of $('run-pipe').options){const run=result.nodes.find(n=>n.id===option.value);option.disabled=kind==='elbolet'?run?.kind!=='elbow'||(run.bendAngle!==90&&run.id!==design.components.find(c=>c.id===selected)?.parentPort.split(':')[0]):run?.kind!=='pipe';}
 for(const option of $('outlet-end').options)if(option.value==='threaded')option.disabled=kind!=='pipe';if(kind!=='pipe'&&$('outlet-end').value==='threaded')$('outlet-end').value='welded';
 $('outlet-end').previousElementSibling.textContent=kind==='tee'?('Terminación '+($('tee-entry').value==='a'?'lado B':'lado A')):'Terminación de salida principal';$('branch-end').previousElementSibling.textContent=kind==='tee'&&$('tee-entry').value==='branch'?'Terminación lado B':'Terminación de derivación de la tee';
 const viaBranch=kind==='tee'&&$('tee-entry').value==='branch';if(viaBranch){$('out-nps').value=nps;$('out-nps').disabled=true;}else $('out-nps').disabled=false;for(const option of $('tee-run-nps').options)option.disabled=Number(option.value)<nps;if(Number($('tee-run-nps').value)<nps)$('tee-run-nps').value=nps;
 $('roll').disabled=['pipe','flange','cap','elbolet'].includes(kind);
 for(const option of $('out-nps').options)option.disabled=['tee','sockolet','thredolet','latrolet','elbolet'].includes(kind)&&Number(option.value)>nps;
 if(['tee','sockolet','thredolet','latrolet','elbolet'].includes(kind)&&Number($('out-nps').value)>nps)$('out-nps').value=nps;
 const spec=item(catalog,nps),f=spec.flanges[$('rating').value];$('dim-info').textContent=`DE cañería: ${spec.odMM} mm · Brida ${$('rating').value}: Ø ${f.diameterMM.toFixed(1)} mm · espesor ${f.thicknessMM.toFixed(1)} mm · ${f.boltCount} pernos.`;
 if(kind==='valve'&&$('valve-connection').value==='threaded')$('dim-info').textContent='Entrada y salida NPT hembra. Para conectarlas se utiliza un niple con rosca macho; las medidas se heredan del extremo elegido.';if(['sockolet','thredolet','latrolet','elbolet'].includes(kind))$('dim-info').textContent='Principal: '+item(catalog,nps).label+' · Salida: '+item(catalog,Number($('out-nps').value)).label+' · '+(kind==='thredolet'?'Rosca NPT':kind==='sockolet'?'Soldadura socket · SW':kind==='latrolet'?'Derivación soldada a 45°':'Derivación soldada en codo');
 $('attach').disabled=!selected||!activePort;$('apply').disabled=!selected;$('delete').disabled=!selected;$('add').disabled=['sockolet','thredolet','latrolet','elbolet'].includes(kind)?!$('run-pipe').value:!activePort;
}
function form(){const source=selected?design.components.find(c=>c.id===selected):null;return {id:source?.id||'c'+uid().slice(0,24),parentPort:['sockolet','thredolet','latrolet','elbolet'].includes($('kind').value)?$('run-pipe').value+':tap':source?.parentPort||activePort,branchYawDeg:Number($('branch-yaw').value),branchPitchDeg:Number($('branch-pitch').value),branchDirection:$('olet-angle').value,tapOffsetMM:$('kind').value==='elbolet'?0:Number($('tap-offset').value),teeEntry:$('tee-entry').value,teeRunNps:Number($('tee-run-nps').value),kind:$('kind').value,tag:$('tag').value.trim()||nextTag($('kind').value),nps:Number($('nps').value),outNps:Number($('out-nps').value),branchNps:Number($('out-nps').value),rating:$('rating').value,outletEnd:$('outlet-end').value,branchEnd:$('branch-end').value,outletRating:$('outlet-rating').value,lengthMM:Number($('length').value),radiusMM:Number($('radius').value),branchLengthMM:Number($('branch-length').value),rollDeg:Number($('roll').value),bendAngle:Number($('bend').value),reduction:$('reduction').value,inletEnd:$('inlet-end').value,valveConnection:$('valve-connection').value,valveType:$('valve-type').value};}
function refresh(){
 $('title').value=design.title;$('direction').value=design.direction;$('direction').disabled=design.components.length>0;$('count').textContent=design.components.length+' componentes';$('project').textContent=design.title;$('empty').hidden=design.components.length>0||(design.equipments||[]).length>0;
 $('port').replaceChildren(...result.freePorts.map(p=>new Option(p.label+(p.nps?' · '+item(catalog,p.nps).label:''),p.id)));$('port').value=activePort;
 const p=result.ports.get(activePort);$('port-info').textContent=p?`X ${p.position[0].toFixed(1)} · Y ${p.position[1].toFixed(1)} · Z ${p.position[2].toFixed(1)} mm${p.endType==='flanged'?' · Enflanchado '+p.rating:''}`:'No quedan extremos abiertos. Selecciona un elemento para modificarlo.';
 const eqid=$('equipment').value;$('equipment').replaceChildren(...(design.equipments||[]).map(e=>new Option(e.tag,e.id)));if((design.equipments||[]).some(e=>e.id===eqid))$('equipment').value=eqid;equipmentForm();
 const run=$('run-pipe').value;$('run-pipe').replaceChildren(...result.nodes.filter(n=>(n.kind==='pipe'||n.kind==='elbow')).map(n=>new Option(n.tag+' · '+item(catalog,n.nps).label+' · '+n.length.toFixed(0)+' mm',n.id)));if(result.nodes.some(n=>(n.kind==='pipe'||n.kind==='elbow')&&n.id===run))$('run-pipe').value=run;
 $('component-list').replaceChildren(...result.nodes.map(n=>new Option(n.tag+' · '+TYPES[n.kind]+(n.kind==='valve'?' '+VALVES[n.valveType]:'')+' · '+item(catalog,n.nps).label,n.id)));$('component-list').value=selected||'';$('undo').disabled=!undo.length;$('redo').disabled=!redo.length;conditional();refreshContinuation();height();
}
function continueFrom(id){clearTimeout(liveTimer);liveSelection=null;activePort=id;selected=null;const parent=id.split(':')[0];continuationId=design.components.some(c=>c.id===parent)?parent:null;defaults();renderModel();refresh();status('Continúa desde '+result.ports.get(id).label+'. Elige el siguiente elemento y pulsa Conectar.');}
function refreshContinuation(){
 const source=[selected,continuationId].find(id=>design.components.some(c=>c.id===id)),ports=result.freePorts.filter(p=>source?p.id.startsWith(source+':'):p.id===activePort);
 $('continuation').replaceChildren(...ports.map(p=>{const button=document.createElement('button');button.type='button';button.textContent='Continuar: '+p.label+' · '+(p.endType==='flanged'?'enflanchado':p.endType==='threaded'?'roscado NPT':'para soldar');button.className=p.id===activePort?'primary':'';button.onclick=()=>continueFrom(p.id);return button;}));
 const host=result.nodes.find(n=>n.id===source);if(host?.kind==='tee'){const free=new Set(result.freePorts.map(p=>p.id));$('continuation').replaceChildren(...['in','out','branch'].map(suffix=>{const id=host.id+':'+suffix,port=result.ports.get(id),entryName=host.teeEntry==='branch'?'derivación':host.teeEntry==='b'?'lado B':'lado A',button=document.createElement('button');button.textContent=(free.has(id)?'Continuar: ':'Ocupada: ')+(port?.label||host.tag+' · '+entryName);button.disabled=!free.has(id);button.className=id===activePort?'primary':'';button.onclick=()=>continueFrom(id);return button;}));}if(host&&(host.kind==='pipe'||host.kind==='elbow'&&host.bendAngle===90)){const button=document.createElement('button');button.textContent=host.kind==='pipe'?'Agregar derivación sobre este tramo':'Agregar derivación al centro del codo';button.onclick=()=>{selected=null;$('kind').value=host.kind==='pipe'?'sockolet':'elbolet';$('run-pipe').value=host.id;defaults();refresh();};$('continuation').append(button);}
 const port=result.ports.get(activePort);$('connection-help').textContent=port?.endType==='threaded'?'Salida NPT '+(port.threadGender==='male'?'macho: conecta una válvula roscada hembra.':'hembra: continúa con un niple de rosca macho.'):port?'Siguiente conexión: '+port.label+'. '+(port.endType==='flanged'?'Se agrega la contraparte enflanchada al continuar con piping.':'La continuación se une por soldadura.'):'Selecciona otro extremo libre para continuar.';
 $('add').textContent=['sockolet','thredolet','latrolet','elbolet'].includes($('kind').value)?'+ Soldar derivación a la línea principal':port?'+ Conectar a '+port.label:'+ Sin extremos libres';
}
function selectNode(id){const component=design.components.find(c=>c.id===id);if(component&&isOlet(component)){$('run-pipe').value=component.parentPort.split(':')[0];$('tap-offset').value=component.tapOffsetMM;$('branch-yaw').value=component.branchYawDeg??0;$('branch-pitch').value=component.branchPitchDeg??0;$('olet-angle').value=component.branchDirection||(component.branchAngle===45?'inlet':'outlet');}continuationId=id;clearTimeout(liveTimer);liveSelection=null;selected=id;selectedEquipmentId=null;const c=design.components.find(c=>c.id===id);if(c){for(const [field,key] of [['outlet-end','outletEnd'],['branch-end','branchEnd'],['tee-entry','teeEntry'],['tee-run-nps','teeRunNps'],['inlet-end','inletEnd'],['valve-connection','valveConnection'],['kind','kind'],['tag','tag'],['nps','nps'],['rating','rating'],['outlet-rating','outletRating'],['length','lengthMM'],['radius','radiusMM'],['branch-length','branchLengthMM'],['roll','rollDeg'],['bend','bendAngle'],['reduction','reduction'],['valve-type','valveType']])$(field).value=c[key]??(key==='inletEnd'?'auto':key==='valveConnection'?'flanged':key==='teeEntry'?'a':key==='teeRunNps'?c.nps:['outletEnd','branchEnd'].includes(key)?'welded':c.rating);$('out-nps').value=c.kind==='tee'?c.branchNps:c.outNps;status('Seleccionado '+c.tag+'. Los cambios se actualizan automáticamente.');}refresh();highlight();}
const wrap=$('viewport'),scene=new THREE.Scene();scene.background=new THREE.Color('#edf3f7');
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));wrap.append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-1000,1000,700,-700,.1,1e7);camera.up.set(0,0,1);camera.position.set(3000,-3000,3000);
const controls=new OrbitControls(camera,renderer.domElement);controls.mouseButtons={LEFT:THREE.MOUSE.ROTATE,MIDDLE:THREE.MOUSE.PAN,RIGHT:THREE.MOUSE.PAN};renderer.domElement.addEventListener('pointerdown',e=>{if(e.button===1)e.preventDefault();});controls.enableDamping=true;controls.dampingFactor=.08;controls.zoomSpeed=.7;controls.panSpeed=.7;controls.minZoom=.02;controls.maxZoom=80;
scene.add(new THREE.HemisphereLight(0xffffff,0x6a8193,2.4));const sun=new THREE.DirectionalLight(0xffffff,2.5);sun.position.set(3,-4,6);scene.add(sun);
const model=new THREE.Group(),portsGroup=new THREE.Group(),labelsGroup=new THREE.Group();scene.add(model,portsGroup,labelsGroup);
const pipeModel=new THREE.Group(),equipmentModel=new THREE.Group();model.add(pipeModel,equipmentModel);
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
function drawFlange(start,axis,f,parent){const rf=f.raisedFaceMM&&f.face!=='FF'? (f.rating==='600#'?6.35:1.5875):0,hub=Math.max(1,f.lengthMM-f.thicknessMM-rf);
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
function equipmentForm(){const e=(design.equipments||[]).find(e=>e.id===$('equipment').value);for(const [id,i] of [['equipment-x',0],['equipment-y',1],['equipment-z',2]])$(id).value=e?.position[i]??0;$('equipment-rotation').value=e?.rotationDeg??0;$('equipment-apply').disabled=!e;$('equipment-remove').disabled=!e;$('equipment-edit').disabled=!e?.sourceDesign;}
function addNameplate(group,e){
 const canvas=document.createElement('canvas');canvas.width=1024;canvas.height=384;const ctx=canvas.getContext('2d');ctx.fillStyle='#102a3b';ctx.fillRect(0,0,1024,384);ctx.strokeStyle='#76d4bd';ctx.lineWidth=12;ctx.strokeRect(14,14,996,356);ctx.textAlign='center';ctx.fillStyle='#76d4bd';ctx.font='36px sans-serif';ctx.fillText('JNDIGITAL · EQUIPO',512,95);ctx.fillStyle='#ffffff';let font=110;do{ctx.font='bold '+font+'px sans-serif';font-=4;}while(ctx.measureText(e.tag).width>920&&font>20);ctx.fillText(e.tag,512,250,920);
 const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;const plate=mesh(new THREE.BoxGeometry(.90,.34,.018),new THREE.MeshBasicMaterial({map:texture}),group);plate.name='Nameplate · '+e.tag;
 if(e.nameplate?.matrix){plate.matrixAutoUpdate=false;plate.matrix.fromArray(e.nameplate.matrix);}else{const box=new THREE.Box3().setFromObject(group),size=box.getSize(new THREE.Vector3()),center=box.getCenter(new THREE.Vector3()),width=Math.min(900,Math.max(250,size.x*.6));plate.scale.set(width/.9,width/.9,width/.9);plate.rotation.x=Math.PI/2;plate.position.set(center.x,box.min.y-12,center.z);}
}
function equipmentKey(e){return e.asset.data.object.uuid+'|'+e.tag+'|'+JSON.stringify(e.nameplate||null);}
function selectEquipment(id){if(!id)return;selected=null;selectedEquipmentId=id;$('equipment').value=id;equipmentForm();highlight();status('Equipo '+(design.equipments||[]).find(e=>e.id===id).tag+' seleccionado. Puedes moverlo aquí o abrir Editar equipo.');}
function syncEquipmentModels(){
 for(const group of [...equipmentModel.children]){const e=(design.equipments||[]).find(e=>e.id===group.userData.equipmentId);if(!e||group.userData.assetKey!==equipmentKey(e)){equipmentModel.remove(group);clear(group);}}
 for(const e of design.equipments||[]){let group=equipmentModel.children.find(g=>g.userData.equipmentId===e.id);if(!group){group=new THREE.Group();group.add(loadAsset(e.asset));group.userData={equipmentId:e.id,assetKey:equipmentKey(e)};addNameplate(group,e);equipmentModel.add(group);}group.position.set(...e.position);group.rotation.z=e.rotationDeg*Math.PI/180;}
}
function drawBallValve(n,f,group){
 const D=n.odMM,axis=n.axis,up=n.normal,side=norm(cross(axis,up));
 const body=mesh(new THREE.SphereGeometry(1,40,28),metal,group);body.name='Cuerpo fundido válvula de bola';body.position.copy(v(n.center));body.scale.set(D*.84,D*.84,Math.max(D*.8,(n.length-2*f.lengthMM)*.46));body.quaternion.setFromUnitVectors(zaxis,v(axis));
 // Uniones del cuerpo partido, con sus espárragos y tuercas visibles.
 const half=Math.min(D*.68,(n.length-2*f.lengthMM)*.32),r=D*.88,t=D*.10;
 for(const sign of [-1,1]){const seat=add(n.center,mul(axis,sign*half));const ring=cylinder(sub(seat,mul(axis,t/2)),add(seat,mul(axis,t/2)),r,metal,group);ring.name='Unión apernada del cuerpo de bola';
  for(let i=0;i<8;i++){const a=(i+.5)*Math.PI/4,offset=add(mul(up,Math.cos(a)*r*.86),mul(side,Math.sin(a)*r*.86)),point=add(seat,offset);cylinder(sub(point,mul(axis,t*1.5)),add(point,mul(axis,t*1.5)),D*.035,nutMat,group);for(const end of [-1,1]){const nut=mesh(new THREE.CylinderGeometry(D*.075,D*.075,D*.075,6),nutMat,group);nut.position.copy(v(add(point,mul(axis,end*t))));nut.quaternion.setFromUnitVectors(yaxis,v(axis));}}
 }
 const neck=add(n.center,mul(up,D*.72)),packing=add(n.center,mul(up,D*1.25)),top=add(n.center,mul(up,D*1.65));
 cylinder(neck,packing,D*.27,metal,group).name='Prensaestopa válvula de bola';cylinder(packing,top,D*.105,nutMat,group).name='Vástago válvula de bola';
 // Mando de la referencia: palanca elevada que termina en un aro vertical.
 const elbow=add(add(top,mul(axis,D*.55)),mul(up,D*.30)),tip=add(elbow,mul(axis,D*2.25));
 cylinder(top,add(top,mul(axis,D*.32)),D*.085,nutMat,group);cylinder(add(top,mul(axis,D*.32)),elbow,D*.085,nutMat,group);cylinder(elbow,tip,D*.085,nutMat,group).name='Palanca válvula de bola';
 const wheel=mesh(new THREE.TorusGeometry(D*.48,D*.065,12,48),nutMat,group);wheel.name='Aro de mando válvula de bola';wheel.position.copy(v(sub(tip,mul(up,D*.42))));wheel.quaternion.setFromUnitVectors(zaxis,v(side));
}
function drawThread(point,axis,od,parent,female=false){
 const length=Math.min(25,Math.max(8,od*.3)),radial=normal(axis),side=cross(axis,radial);
 if(female){const profile=[[od*.48,0],[od*.70,0],[od*.70,length],[od*.48,length],[od*.48,0]].map(([r,y])=>new THREE.Vector2(r,y));const socket=mesh(new THREE.LatheGeometry(profile,48),valveMat,parent);socket.position.copy(v(point));socket.quaternion.setFromUnitVectors(yaxis,v(axis));socket.name='Conexión hembra NPT';}
 const curve=new THREE.Curve();curve.getPoint=t=>v(add(add(point,mul(axis,t*length)),add(mul(radial,Math.cos(t*Math.PI*12)*od*(female?.485:.505)),mul(side,Math.sin(t*Math.PI*12)*od*(female?.485:.505)))));const thread=mesh(new THREE.TubeGeometry(curve,96,Math.max(.55,od*.012),6,false),nutMat,parent);thread.name=female?'Rosca hembra NPT':'Rosca macho NPT';
}
function drawValve(n,f,group){
 const threaded=n.valveConnection==='threaded';if(threaded)f={...f,lengthMM:n.odMM*.4};
 if(threaded)drawThread(n.start,n.axis,n.odMM,group,true);else drawFlange(add(n.start,mul(n.axis,f.lengthMM)),mul(n.axis,-1),f,group);
 const out=threaded?{...f,lengthMM:item(catalog,n.endNps).odMM*.4}:isRelief(n)?{...n.outletFlange,rating:n.endRating}:f,finish=sub(n.end,mul(n.endAxis,out.lengthMM));if(threaded)drawThread(n.end,mul(n.endAxis,-1),item(catalog,n.endNps).odMM,group,true);else drawFlange(finish,n.endAxis,out,group);
 if(isRelief(n)){
  tube(add(n.start,mul(n.axis,f.lengthMM)),n.center,n.odMM,group,valveMat);tube(n.center,finish,item(catalog,n.endNps).odMM,group,valveMat);
  const body=mesh(new THREE.SphereGeometry(n.odMM*.9,32,24),valveMat,group);body.position.copy(v(n.center));
  const bottom=add(n.center,mul(n.axis,n.odMM)),top=add(n.start,mul(n.axis,n.length-n.odMM*.5));cylinder(bottom,top,n.odMM*.07,nutMat,group);
  const a=normal(n.axis),b=cross(n.axis,a),height=Math.hypot(...sub(top,bottom));
  for(const t of [-1,1])for(const u of [-1,1]){const offset=add(mul(a,n.odMM*.52*t),mul(b,n.odMM*.52*u));cylinder(add(bottom,offset),add(top,offset),n.odMM*.045,metal,group);}
  for(const p of [bottom,top])cylinder(sub(p,mul(n.axis,10)),add(p,mul(n.axis,10)),n.odMM*.8,valveMat,group);
  const curve=new THREE.Curve();curve.getPoint=t=>v(add(add(bottom,mul(n.axis,height*t)),add(mul(a,Math.cos(t*Math.PI*18)*n.odMM*.36),mul(b,Math.sin(t*Math.PI*18)*n.odMM*.36))));mesh(new THREE.TubeGeometry(curve,144,n.odMM*.045,8,false),nutMat,group);
  cylinder(top,add(n.start,mul(n.axis,n.length)),n.odMM*.4,valveMat,group);const leverBase=add(n.center,mul(n.normal,-n.odMM*1.05)),leverTop=add(leverBase,mul(n.axis,n.length*.28));cylinder(leverBase,leverTop,n.odMM*.045,nutMat,group).name='Palanca lateral '+n.valveType.toUpperCase();return;
 }
 tube(add(n.start,mul(n.axis,f.lengthMM)),finish,n.odMM,group,valveMat);
 if(n.valveType==='ball'){drawBallValve(n,f,group);return;}
 const body=mesh(['globe','check'].includes(n.valveType)?new THREE.SphereGeometry(n.odMM*.85,32,24):n.valveType==='butterfly'?new THREE.CylinderGeometry(n.odMM*.95,n.odMM*.95,n.odMM*.35,40):new THREE.BoxGeometry(n.odMM*1.8,n.odMM*1.4,n.odMM*1.8),valveMat,group);body.position.copy(v(n.center));body.quaternion.setFromUnitVectors(yaxis,v(n.axis));
 if(n.valveType==='check'){cylinder(add(n.center,mul(n.normal,n.odMM*.65)),add(n.center,mul(n.normal,n.odMM)),n.odMM*.7,flangeMat,group);return;}
 const stemStart=add(n.center,mul(n.normal,n.odMM*.6)),stemEnd=add(n.center,mul(n.normal,n.odMM*2.5));cylinder(stemStart,stemEnd,n.odMM*.09,nutMat,group);
 if(['gate','globe'].includes(n.valveType)){cylinder(stemStart,add(n.center,mul(n.normal,n.odMM*1.5)),n.odMM*.35,valveMat,group);const wheel=mesh(new THREE.TorusGeometry(n.odMM*.7,n.odMM*.07,10,40),valveMat,group);wheel.position.copy(v(stemEnd));wheel.quaternion.setFromUnitVectors(zaxis,v(n.normal));for(const a of [0,Math.PI/2]){const side=add(mul(n.axis,Math.cos(a)*n.odMM*.65),mul(cross(n.normal,n.axis),Math.sin(a)*n.odMM*.65));cylinder(sub(stemEnd,side),add(stemEnd,side),n.odMM*.04,valveMat,group);}}
 else cylinder(stemEnd,add(stemEnd,mul(n.axis,n.odMM*2)),n.odMM*.10,valveMat,group);
}
function drawElbolet(n,group){
 const host=n.origin.elbowSurface,od=item(catalog,n.outNps).odMM,axis=n.axis,u=normal(axis),b=cross(axis,u),steps=64;
 const baseR=Math.min(od*.78,host.odMM*.40),bore=Math.min(od*.42,baseR*.78),outer=od/2;
 function direction(a){return add(mul(u,Math.cos(a)),mul(b,Math.sin(a)));}
 const rings=[],seat=[];
 for(let ring=0;ring<6;ring++){const points=[];for(let i=0;i<=steps;i++){const d=direction(i*2*Math.PI/steps);let point;
  if(ring===0||ring===5){const offset=add(n.runCenter,mul(d,ring===0?baseR:bore));point=add(offset,mul(axis,elbowSeat(offset,axis,host)));if(ring===0)seat.push(v(point));}
  else{const radius=ring===1?Math.max(outer,baseR*.82):ring===2?outer:bore,center=ring===1?add(n.start,mul(axis,n.length*.36)):ring===2||ring===3?n.end:add(n.start,mul(axis,n.length*.36));point=add(center,mul(d,radius));}
  points.push(point);}rings.push(points);}
 const positions=[],indices=[];for(const ring of rings)for(const point of ring)positions.push(...point);
 for(let ring=0;ring<rings.length;ring++){const next=(ring+1)%rings.length;for(let i=0;i<steps;i++){const a=ring*(steps+1)+i,c=next*(steps+1)+i;indices.push(a,c,a+1,a+1,c,c+1);}}
 const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.setIndex(indices);geometry.computeVertexNormals();const fitting=mesh(geometry,metal,group);fitting.name='Elbolet hueco con base adaptada al codo';
 const weldPath=new THREE.CatmullRomCurve3(seat.slice(0,-1),true);const weld=mesh(new THREE.TubeGeometry(weldPath,96,Math.max(1.5,od*.035),8,true),nutMat,group);weld.name='Soldadura siguiendo superficie del codo';
}
function openElboletBores(geometry,elbow){
 const fittings=result.nodes.filter(n=>n.kind==='elbolet'&&n.parentPort===elbow.id+':tap');if(!fittings.length)return geometry;
 const position=geometry.getAttribute('position'),index=geometry.getIndex(),kept=[];
 for(let i=0;i<index.count;i+=3){const ids=[index.getX(i),index.getX(i+1),index.getX(i+2)],point=[0,0,0];for(const id of ids){point[0]+=position.getX(id)/3;point[1]+=position.getY(id)/3;point[2]+=position.getZ(id)/3;}
  const cut=fittings.some(n=>{const od=item(catalog,n.outNps).odMM,bore=Math.min(od*.42,Math.min(od*.78,n.odMM*.40)*.78),q=sub(point,n.runCenter),along=dot(q,n.axis);return along>0&&Math.hypot(...sub(q,mul(n.axis,along)))<bore*.98;});if(!cut)kept.push(...ids);
 }
 geometry.setIndex(kept);return geometry;
}
function renderModel(){
 clear(pipeModel);clear(portsGroup);clear(labelsGroup);syncEquipmentModels();
 for(const n of result.nodes){const group=new THREE.Group();group.userData.id=n.id;pipeModel.add(group);const f={...n.flange,rating:n.rating};
  if(n.outletEndFlange)drawFlange(n.end,n.endAxis,{...n.outletEndFlange,rating:n.rating},group);
  if(n.branch?.flangeSpec)drawFlange(n.branch.bodyPosition,n.branch.axis,{...n.branch.flangeSpec,rating:n.rating},group);
  if(n.adapter)drawFlange(n.adapter.start,n.adapter.axis,f,group);
  if(n.origin.id!=='origin'&&n.origin.endType==='plain'){const weld=mesh(new THREE.TorusGeometry(item(catalog,n.origin.nps??n.nps).odMM/2,Math.max(1.3,n.odMM*.018),8,40),nutMat,group);weld.name='Cordón de soldadura';weld.position.copy(v(n.origin.position));weld.quaternion.setFromUnitVectors(zaxis,v(n.axis));}
  if(n.origin.endType==='flanged'){bolts(add(n.origin.position,mul(n.axis,1.5)),n.axis,f,group);}else if(n.adapter&&!n.adapter.reverse){bolts(add(n.adapter.start,mul(n.axis,f.lengthMM+1.5)),n.axis,f,group);}
  if(n.kind==='elbolet')drawElbolet(n,group);
  else if(isOlet(n)){const od=item(catalog,n.outNps).odMM;const neck=add(n.start,mul(n.axis,n.length*.65));cylinder(n.start,neck,od*.88,metal,group,od*.57);tube(neck,n.end,od,group);if(n.kind==='thredolet'){for(let i=0;i<5;i++){const thread=mesh(new THREE.TorusGeometry(od*.43,Math.max(.8,od*.012),6,32),nutMat,group);thread.name='Rosca NPT thredolet';thread.position.copy(v(sub(n.end,mul(n.axis,2+i*2))));thread.quaternion.setFromUnitVectors(zaxis,v(n.axis));}}const weld=mesh(new THREE.TorusGeometry(od*.85,Math.max(2,od*.055),10,40),nutMat,group);weld.name='Soldadura sockolet a línea principal';weld.position.copy(v(n.start));weld.quaternion.setFromUnitVectors(zaxis,v(n.axis));}
  else if(n.kind==='pipe'){tube(n.start,n.end,n.odMM,group);if(n.inletType==='threaded')drawThread(n.start,n.axis,n.odMM,group);if(n.endType==='threaded')drawThread(n.end,mul(n.endAxis,-1),n.odMM,group);}
  else if(n.kind==='elbow'){const R=Math.max(n.radiusMM,n.odMM*.6),angle=n.bendAngle*Math.PI/180,path=new THREE.Curve();path.getPoint=t=>v(add(n.start,add(mul(n.axis,R*Math.sin(angle*t)),mul(n.normal,R*(1-Math.cos(angle*t))))));mesh(openElboletBores(new THREE.TubeGeometry(path,96,n.odMM/2,64,false),n),metal,group);}
  else if(n.kind==='tee'){tube(n.teeA,n.teeB,n.odMM,group);tube(n.center,n.teeLegEnd,item(catalog,n.branchNps).odMM,group);}
  else if(n.kind==='reducer')reducer(n,group);
  else if(n.kind==='flange')drawFlange(n.reverse?n.end:n.start,n.reverse?mul(n.axis,-1):n.axis,f,group);
  else if(n.kind==='cap')plate(n.start,n.axis,f,group,true);
  else if(n.kind==='valve')drawValve(n,f,group);
 }
 const box=new THREE.Box3().setFromObject(model);totalSize=box.isEmpty()?1500:Math.max(box.getSize(new THREE.Vector3()).length(),500);grid.position.z=box.isEmpty()?-1:box.min.z-40;
 for(const e of design.equipments||[]){const group=equipmentModel.children.find(g=>g.userData.equipmentId===e.id),box=new THREE.Box3().setFromObject(group),center=box.getCenter(new THREE.Vector3());label(e.tag,[center.x,center.y,box.max.z+totalSize*.04]);}
 for(const n of result.nodes){const shift=Math.max(n.odMM*(n.kind==='valve'?3.3:1.3),totalSize*.06),point=add(n.center,mul(n.normal,shift));const sprite=label(n.tag+(n.kind==='pipe'?' · '+n.length.toFixed(0)+' mm':''),point);const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints([v(n.center),v(point)]),new THREE.LineBasicMaterial({color:0x607e90,transparent:true,opacity:.8,depthTest:false}));sprite.userData.line=line;sprite.userData.center=[...n.center];labelsGroup.add(line);}
 for(const p of result.freePorts){if(p.id!=='origin')label(p.label,add(p.position,mul(normal(p.axis),Math.max(80,totalSize*.035))));const r=Math.max(8,Math.min(40,totalSize*.012)),m=mesh(new THREE.SphereGeometry(r,20,16),new THREE.MeshStandardMaterial({color:p.id===activePort?0xf7a73b:0x20b99d,emissive:p.id===activePort?0x422200:0x003329}),portsGroup);m.position.copy(v(p.position));m.userData.portId=p.id;}
 labelsGroup.visible=labelsVisible;grid.scale.setScalar(Math.max(1,totalSize/6000));axes.scale.setScalar(Math.max(1,totalSize/2000));highlight();fit('current');
}
function highlight(){model.traverse(o=>{if(o.isMesh&&o.material){const id=o.parent?.userData.id;/* Materiales compartidos se mantienen neutros; la selección usa un recuadro. */}});const old=scene.getObjectByName('selection-box');if(old){scene.remove(old);old.geometry.dispose();old.material.dispose();}if(selected||selectedEquipmentId){const group=selected?pipeModel.children.find(g=>g.userData.id===selected):equipmentModel.children.find(g=>g.userData.equipmentId===selectedEquipmentId);if(group){const box=new THREE.BoxHelper(group,0x0c9b87);box.name='selection-box';scene.add(box);}}}
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
new ResizeObserver(resize).observe(wrap);$('panel').addEventListener('toggle',()=>{setTimeout(resize,50);height();});
let down=null;renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;const rect=renderer.domElement.getBoundingClientRect(),mouse=new THREE.Vector2((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1),ray=new THREE.Raycaster();ray.setFromCamera(mouse,camera);const ports=ray.intersectObjects(portsGroup.children);if(ports.length){continueFrom(ports[0].object.userData.portId);return;}const hits=ray.intersectObjects(model.children,true);if(hits.length){let node=hits[0].object;while(node&&!node.userData.id&&!node.userData.equipmentId)node=node.parent;if(node?.userData.id)selectNode(node.userData.id);else if(node?.userData.equipmentId){selectEquipment(node.userData.equipmentId);}}});
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
let liveTimer=null,liveUndoTimer=null,liveSelection=null;
function updateSelected(){
 clearTimeout(liveTimer);if(!selected)return true;const current=design.components.find(c=>c.id===selected);if(!current)return true;
 const edited=form();if(JSON.stringify(current)===JSON.stringify(edited))return true;
 try{const next=structuredClone(design);next.components[next.components.findIndex(c=>c.id===selected)]=edited;next.components=sortComponents(next,catalog).components;setDesign(next,liveSelection!==selected);liveSelection=selected;clearTimeout(liveUndoTimer);liveUndoTimer=setTimeout(()=>{liveSelection=null;},800);status('Cambios actualizados en '+edited.tag+'.');return true;}catch(error){status(error.message,true);return false;}
}
for(const id of ['inlet-end','valve-connection','tee-entry','tee-run-nps','branch-yaw','branch-pitch','olet-angle','run-pipe','tap-offset','outlet-end','branch-end','tag','nps','rating','out-nps','outlet-rating','length','radius','branch-length','roll','bend','reduction','valve-type']){
 $(id).addEventListener('input',()=>{clearTimeout(liveTimer);if(selected)liveTimer=setTimeout(updateSelected,160);});
 $(id).addEventListener('change',()=>{if(selected)updateSelected();});
}
$('add').onclick=guard(()=>{if(!activePort&&!['sockolet','thredolet','latrolet','elbolet'].includes($('kind').value))throw Error('No hay un extremo libre.');const c=form();c.id='c'+uid().slice(0,24);if(!isOlet(c))c.parentPort=activePort;if(!mutate(d=>d.components.push(c)))return;selected=null;continuationId=c.id;if(isOlet(c))$('kind').value='pipe';activePort=result.freePorts.find(p=>p.id===c.id+':out')?.id||result.freePorts.at(-1)?.id||'';defaults();renderModel();refresh();status(c.kind==='cap'?'Extremo cerrado. Elige otro extremo libre para continuar.':c.kind==='tee'?'Tee agregada. Elige lado A, lado B o derivación entre las bocas libres.':'Elemento conectado. Puedes continuar desde su salida o elegir otro extremo libre.');});
$('apply').onclick=()=>{if(!selected)return;const c=form();if(mutate(d=>{d.components[d.components.findIndex(n=>n.id===selected)]=c;}))selectNode(selected);};
$('delete').onclick=()=>{if(!selected)return;const ids=descendants(design,selected);if(ids.size>1&&!confirm('Se eliminarán '+ids.size+' componentes, incluyendo las continuaciones. Puedes deshacerlo.'))return;mutate(d=>{d.components=d.components.filter(c=>!ids.has(c.id));});selected=null;defaults();refresh();};
$('clear').onclick=()=>{selected=null;defaults();refresh();highlight();};$('valve-connection').onchange=conditional;$('tee-entry').onchange=()=>{conditional();height();};$('olet-angle').onchange=()=>{conditional();height();};$('run-pipe').onchange=()=>{const run=result.nodes.find(n=>n.id===$('run-pipe').value);if(run){$('tap-offset').max=run.length;if(!selected)$('tap-offset').value=run.length/2;}conditional();refreshContinuation();};$('kind').onchange=()=>{if(['psv','rv'].includes($('kind').value)){$('valve-type').value=$('kind').value;$('kind').value='valve';}if(selected){conditional();updateSelected();}else defaults();};$('nps').onchange=()=>{if(selected){conditional();updateSelected();}else defaults();};$('rating').onchange=conditional;$('valve-type').onchange=conditional;$('port').onchange=()=>{activePort=$('port').value;if(!selected)defaults();renderModel();refresh();};$('component-list').onchange=()=>selectNode($('component-list').value);
$('equipment').onchange=()=>selectEquipment($('equipment').value);$('equipment-edit').onclick=()=>{if(equipmentTimer){clearTimeout(equipmentTimer);equipmentTimer=null;$('equipment-apply').click();}const id=$('equipment').value;if(!id)return;notify('edit_equipment',{equipmentId:id,eventId:uid()});};
$('equipment-apply').onclick=()=>mutate(d=>{const e=d.equipments.find(e=>e.id===$('equipment').value);e.position=['equipment-x','equipment-y','equipment-z'].map(id=>Number($(id).value));e.rotationDeg=Number($('equipment-rotation').value);});
let equipmentTimer=null;for(const id of ['equipment-x','equipment-y','equipment-z','equipment-rotation'])$(id).addEventListener('input',()=>{clearTimeout(equipmentTimer);equipmentTimer=setTimeout(()=>{equipmentTimer=null;if(['equipment-x','equipment-y','equipment-z','equipment-rotation'].every(k=>$(k).value.trim()!==''))$('equipment-apply').click();},180);});
$('equipment-remove').onclick=()=>mutate(d=>{const id=$('equipment').value;if(d.components.some(c=>c.parentPort.startsWith('eq-'+id+'/')))throw Error('Desacopla o elimina primero las líneas conectadas al equipo.');d.equipments=d.equipments.filter(e=>e.id!==id);});
$('attach').onclick=()=>{if(!selected||!activePort)return;const target=activePort,id=selected;if(mutate(d=>{const c=d.components.find(c=>c.id===id);c.parentPort=target;d.components=sortComponents(d,catalog).components;}))status('Línea acoplada al extremo seleccionado, incluyendo su continuación.');};
$('title').onchange=()=>mutate(d=>{d.title=$('title').value.trim()||'Línea de piping';});$('direction').onchange=()=>mutate(d=>{d.direction=$('direction').value;});
$('undo').onclick=()=>{clearTimeout(liveTimer);liveSelection=null;if(!undo.length)return;redo.push(structuredClone(design));const d=undo.pop();selected=null;setDesign(d,false);defaults();};$('redo').onclick=()=>{clearTimeout(liveTimer);liveSelection=null;if(!redo.length)return;undo.push(structuredClone(design));const d=redo.pop();selected=null;setDesign(d,false);defaults();};
$('save').onclick=guard(()=>{
 if(updateSelected()===false)throw Error('Corrige los valores del componente antes de guardar el proyecto.');
 if(equipmentTimer){clearTimeout(equipmentTimer);equipmentTimer=null;if(['equipment-x','equipment-y','equipment-z','equipment-rotation'].some(id=>$(id).value.trim()===''))throw Error('Completa la posición del equipo antes de guardar.');if($('equipment-apply').onclick()===false)throw Error('Revisa la posición del equipo antes de guardar.');}
 validateDesign(design,catalog);const now=new Date(),stamp=now.getFullYear()+'-'+String(now.getMonth()+1).padStart(2,'0')+'-'+String(now.getDate()).padStart(2,'0')+'_'+String(now.getHours()).padStart(2,'0')+'-'+String(now.getMinutes()).padStart(2,'0')+'-'+String(now.getSeconds()).padStart(2,'0');
 lastBackupFile=filename()+'_'+stamp+'.json';exportFile(lastBackupFile,JSON.stringify(design,null,2),'application/json');lastBackupAt=now.toLocaleString('es-CL');backupInfo(false);status('Respaldo completo preparado: '+(design.equipments||[]).length+' equipos y '+design.components.length+' componentes. Revisa la descarga del archivo JSON.');
});$('load').onclick=()=>$('file').click();$('file').onchange=guard(async()=>{const f=$('file').files[0];if(!f)return;if(f.size>32e6)throw Error('El JSON supera 32 MB.');setDesign(JSON.parse(await f.text()));selected=null;defaults();refresh();status('Proyecto abierto: '+(design.equipments||[]).length+' equipos y '+design.components.length+' componentes. Puedes continuar editando.');backupInfo();$('file').value='';});
$('example').onclick=guard(async()=>{if((design.components.length||(design.equipments||[]).length)&&!confirm('¿Abrir el ejemplo? Podrás recuperar el diseño actual con Deshacer.'))return;selected=null;setDesign(await fetch('./ejemplo.json').then(r=>r.json()));activePort=result.freePorts.at(-1)?.id||'';defaults();refresh();fit('iso');status('Ejemplo cargado. Selecciona un elemento para editarlo o continúa desde un extremo.');});
$('new').onclick=()=>{if((design.components.length||(design.equipments||[]).length)&&!confirm('¿Comenzar una línea nueva? Descarga antes el JSON si deseas conservar la actual.'))return;selected=null;activePort='origin';setDesign(blankDesign('p'+uid()));defaults();refresh();};
for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>fit(b.dataset.view==='fit'?'current':b.dataset.view);
$('labels').onclick=()=>{labelsVisible=!labelsVisible;labelsGroup.visible=labelsVisible;$('labels').textContent=labelsVisible?'Ocultar TAG':'Mostrar TAG';};
$('png').onclick=guard(async()=>{const data=await capture();const a=document.createElement('a');a.href=data;a.download=filename()+'.png';a.click();});
$('pdf').onclick=guard(async()=>{if(!design.components.length&&!(design.equipments||[]).length)throw Error('Agrega componentes o equipos antes de exportar.');status('Preparando isométrico y materiales…');notify('export_pdf',{image:await capture()});status('Captura lista. Descarga el PDF debajo del editor.');});
window.addEventListener('message',e=>{if(e.data.type!=='streamlit:render')return;serverArgs=e.data.args||{};const initialize=!loaded||loadToken!==serverArgs.load_token;loadToken=serverArgs.load_token;loaded=true;
 try{if(initialize){let initial=serverArgs.initial_data||blankDesign();if(!serverArgs.imported){try{const saved=JSON.parse(localStorage.getItem(STORAGE));if(saved?.version===1&&(!initial.components.length||saved.updatedAt>initial.updatedAt))initial=saved;}catch{}}
 validateDesign(initial,catalog);for(const e of initial.equipments||[])validateAsset(e.asset);design=structuredClone(initial);result=compute(design,catalog);activePort=result.freePorts.at(-1)?.id||'';selected=null;renderModel();refresh();$('nps').value=2;defaults();notify();status('Diseño listo. El respaldo automático se conserva en este navegador.');}
 if(serverArgs.equipment_import&&serverArgs.equipment_import_token!==design.equipmentImportToken){const token=serverArgs.equipment_import_token,e=serverArgs.equipment_import;const ok=mutate(d=>{d.equipments ||= [];const i=d.equipments.findIndex(old=>old.id===e.id);if(i>=0)d.equipments[i]={...e,position:d.equipments[i].position,rotationDeg:d.equipments[i].rotationDeg};else d.equipments.push(e);d.equipmentImportToken=token;});if(ok){notify('equipment_applied',{equipmentApplied:token});status('Equipo incorporado. Elige una boquilla para continuar el piping.');}else notify('equipment_error',{equipmentApplied:token});}
 else if(serverArgs.equipment_import_token&&serverArgs.equipment_import_token===design.equipmentImportToken)notify('equipment_applied',{equipmentApplied:design.equipmentImportToken});
 }catch(err){status(err.message,true);}
});
function animate(){requestAnimationFrame(animate);controls.update();arrangeLabels();renderer.render(scene,camera);}animate();renderModel();refresh();$('nps').value=2;defaults();send('streamlit:componentReady',{apiVersion:1});height();
// Inspección de geometría sin datos privados para pruebas y soporte.
window.pipingEditor={getDesign:()=>structuredClone(design),getResult:()=>result,load:d=>setDesign(d),capture,scene,camera,model,renderer};
