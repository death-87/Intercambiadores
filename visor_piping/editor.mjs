import {drawPoncho as drawPonchoGeometry} from './poncho_view.mjs';
import {reducerSection} from './reducer_profile.mjs';
import {pipeFrame,pipeDistance} from './pipe_path.mjs';
import {splitPipe,removeWeld} from './split_pipe.mjs';
import {REPAIRS,componentCoordinates,removeDetails} from './details.mjs';
import {drawRepairs,createAnnotations,arrangeAnnotations} from './details_view.mjs';
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {add,sub,mul,dot,norm,normal,cross,blankDesign,compute,validateDesign,descendants,item,materialRows,TYPES,VALVES,isRelief,isOlet} from './model.mjs';
import {elbowSeat} from './elbow_surface.mjs';
import {saveLocal,listLocal} from './projects.mjs';
import {adaptValveEdit} from './valve_edit.mjs';
import {sortComponents} from './equipment.mjs';
import {loadAsset,validateAsset} from './assets.mjs';
const kindValue=()=>['reducer-concentric','reducer-eccentric'].includes(document.getElementById('kind').value)?'reducer':document.getElementById('kind').value;
const $=id=>document.getElementById(id),catalog=await fetch('./catalogo.json').then(r=>r.json());
const uid=()=>((globalThis.crypto?.randomUUID?.()||Date.now().toString(36)+Math.random().toString(36).slice(2)).replaceAll('-',''));
let selectedRepairId=null,selectedAnnotationId=null,marking=false,weldMode=false,detailTimer=null;
const STORAGE='jndigital.piping.design.v1';let design=blankDesign(),result=compute(design,catalog),selected=null,selectedEquipmentId=null,continuationId=null,activePort='origin',undo=[],redo=[],loaded=false,loadToken=null,timer=null,labelsVisible=true,serverArgs={},storageWarning='';
const send=(type,data={})=>window.parent.postMessage({isStreamlitMessage:true,type,...data},'*');
function height(){send('streamlit:setFrameHeight',{height:Math.max(880,document.body.scrollHeight+8)});}
function status(text,error=false){$('status').textContent=text+(storageWarning&&!error?' · '+storageWarning:'');$('status').classList.toggle('error',error||!!storageWarning);}
function notify(action='update',extra={}){clearTimeout(timer);const transmit=()=>send('streamlit:setComponentValue',{value:{action,token:loadToken,design:structuredClone(design),materials:materialRows(result,catalog),...extra},dataType:'json'});if(action==='update')timer=setTimeout(transmit,350);else transmit();}
let lastBackupAt=null,lastBackupFile='',pendingCloud=null,lastProjectAck=null;function backupInfo(dirty=true){$('backup-info').textContent=dirty?(lastBackupAt?'Hay cambios posteriores a la última copia. ':'')+'Guarda el proyecto por nombre en Mis proyectos. El guardado local pertenece a este navegador; Google Drive permite continuar en otro computador.':'Copia preparada el '+lastBackupAt+'. Archivo: '+lastBackupFile+'. Revisa Descargas y conserva el archivo JSON. Para continuar en otro computador, abre ese archivo; esta copia no se guarda en la nube.';}
function persist(){backupInfo();design.updatedAt=new Date().toISOString();try{localStorage.setItem(STORAGE,JSON.stringify(design));storageWarning='';}catch{storageWarning='El respaldo automático rápido no está disponible. Usa Guardar proyecto o descarga una copia JSON.';status(storageWarning,true);}notify();}
function setDesign(next,record=true,reframe=false){const wasEmpty=!design.components.length&&!design.equipments?.length;validateDesign(next,catalog);for(const e of next.equipments||[])validateAsset(e.asset);const layout=compute(next,catalog);if(record){undo.push(structuredClone(design));if(undo.length>30)undo.shift();redo=[];}design=next;result=layout;selected=design.components.some(c=>c.id===selected)?selected:null;if(!result.freePorts.some(p=>p.id===activePort))activePort=result.freePorts.at(-1)?.id||'';refresh();persist();renderModel();if(reframe||(wasEmpty&&(design.components.length||design.equipments?.length)))fit('current');}
function mutate(fn){try{const next=structuredClone(design);fn(next);setDesign(next);return true;}catch(e){status(e.message,true);return false;}}
function exportFile(name,content,mime){const url=URL.createObjectURL(new Blob([content],{type:mime})),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function filename(){return (design.title||'Piping').replace(/[^\p{L}\p{N}_.-]+/gu,'_').slice(0,100);}
function nextTag(kind){const prefix=kind==='valve'&&['psv','rv'].includes($('valve-type').value)?$('valve-type').value.toUpperCase():{pipe:'P',elbow:'C',tee:'T',poncho:'PR',sockolet:'SO',thredolet:'TH',latrolet:'LO',elbolet:'EO',reducer:'R',valve:'V',flange:'F',cap:'BC',gauge:'PI'}[kind];let n=1;while(design.components.some(c=>c.tag===prefix+String(n).padStart(2,'0')))n++;return prefix+String(n).padStart(2,'0');}
for(const id of ['nps','out-nps','tee-run-nps'])for(const row of catalog.items)$(id).add(new Option(row.label,row.nps));
function context(){if(['sockolet','thredolet','latrolet','elbolet','poncho'].includes(kindValue()))return result.ports.get($('run-pipe').value+':tap');return selected?result.nodes.find(n=>n.id===selected)?.origin:result.ports.get(activePort);}
function defaults(){for(const id of ['pipe-x','pipe-y','pipe-z','pipe-yaw','pipe-pitch','pipe-curve','pipe-curve-roll'])$(id).value=0;const kind=kindValue();let host=result.nodes.find(n=>n.id===$('run-pipe').value);if(['sockolet','thredolet','latrolet','elbolet','poncho'].includes(kind)&&(host?.kind!==(kind==='elbolet'?'elbow':'pipe')||(kind==='elbolet'&&host.bendAngle!==90))){$('run-pipe').value=result.nodes.find(n=>n.kind===(kind==='elbolet'?'elbow':'pipe')&&(kind!=='elbolet'||n.bendAngle===90))?.id||'';}const p=context(),nps=p?.nps||Number($('nps').value)||2,od=item(catalog,nps).odMM;$('nps').value=nps;$('tag').value=nextTag(kind);$('out-nps').value=nps;$('length').value=kind==='pipe'?1000:kind==='gauge'?Number((4*Math.max(32,od*.9)).toFixed(1)):kind==='valve'?Math.max(300,od*6):Math.max(100,od*3);$('radius').value=(nps*25.4*1.5).toFixed(2);$('branch-length').value=Math.max(75,od*1.5).toFixed(1);$('roll').value=0;$('tee-entry').value='a';$('tee-run-nps').value=nps;$('outlet-end').value=kind==='elbow'&&p?.threadGender==='male'?'threaded':'welded';$('branch-end').value='welded';$('inlet-end').value='auto';$('valve-connection').value=p?.endType==='threaded'?'threaded':'flanged';if(['sockolet','thredolet','latrolet','elbolet','poncho'].includes(kind)){const run=result.nodes.find(n=>n.id===$('run-pipe').value);if(run){$('tap-offset').value=run.length/2;$('tap-offset').max=run.length;$('length').value=100;}}if(kind==='poncho'){const out=catalog.items.filter(r=>r.nps<nps).filter(r=>r.nps<=nps/2).at(-1)||catalog.items.find(r=>r.nps<nps);$('out-nps').value=out?.nps||nps;$('pad-length').value=Math.max(250,item(catalog,Number($('out-nps').value)).odMM*2);$('pad-thickness').value=6;$('pad-coverage').value=160;}conditional();refreshContinuation();}
function conditional(){const root=(selected?design.components.find(c=>c.id===selected)?.parentPort:activePort)==='origin';for(const id of ['pipe-x','pipe-y','pipe-z'])$(id).disabled=!root;$('pipe-position-help').textContent=root?'Mueve el inicio libre y toda su continuación conectada.':'La posición está fijada por la conexión anterior. Edita su dirección o mueve el equipo / tramo inicial.';const kind=kindValue(),relief=kind==='valve'&&['psv','rv'].includes($('valve-type').value),p=context(),nps=p?.nps??Number($('nps').value);$('nps').disabled=p?.nps!==null&&p?.nps!==undefined;if(p?.nps)$('nps').value=p.nps;
 $('rating').disabled=kind==='gauge'||p?.endType==='flanged'||kind==='valve'&&$('valve-connection').value==='threaded';if(p?.endType==='flanged')$('rating').value=p.rating;
 for(const [id,on] of [['poncho-row',kind==='poncho'],['pipe-shape-row',kind==='pipe'],['tee-entry-row',kind==='tee'],['tee-run-row',kind==='tee'&&$('tee-entry').value==='branch'],['out-row',['reducer','tee','sockolet','thredolet','latrolet','elbolet','poncho'].includes(kind)||relief],['length-row',!['elbow','flange','cap'].includes(kind)],['elbow-row',kind==='elbow'],['branch-row',kind==='tee'||relief],['outlet-rating-row',relief&&$('valve-connection').value!=='threaded'],['sockolet-row',['sockolet','thredolet','latrolet','elbolet','poncho'].includes(kind)],['olet-angle-row',kind==='elbolet'],['elbolet-rotation-row',kind==='elbolet'&&$('olet-angle').value==='custom'],['ends-row',['pipe','elbow','tee','reducer'].includes(kind)],['branch-end-row',kind==='tee'],['reducer-row',kind==='reducer'],['valve-row',kind==='valve'],['pipe-inlet-row',kind==='pipe']])$(id).hidden=!on;
 $('length-row').querySelector('label').textContent=kind==='gauge'?'Diámetro exterior del manómetro (mm)':['sockolet','thredolet','latrolet','elbolet','poncho'].includes(kind)?'Altura de la derivación sobre la línea (mm)':relief?'Altura total PSV / RV (mm)':kind==='pipe'?'Largo desarrollado del tubo (mm)':'Largo axial / entre caras (mm)';$('branch-row').querySelector('label').textContent=relief?'Largo de salida lateral al eje (mm)':'Largo al eje de derivación (mm)';
 $('tap-offset').disabled=kind==='elbolet';if(kind==='elbolet')$('tap-offset').value=0;for(const option of $('run-pipe').options){const run=result.nodes.find(n=>n.id===option.value);option.disabled=kind==='elbolet'?run?.kind!=='elbow'||(run.bendAngle!==90&&run.id!==design.components.find(c=>c.id===selected)?.parentPort.split(':')[0]):run?.kind!=='pipe';}
 const threadOption=$('outlet-end').querySelector('option[value=threaded]');
 threadOption.disabled=!['pipe','elbow'].includes(kind);
 threadOption.textContent=kind==='elbow'?'Roscadas NPT hembra en ambos extremos':'Rosca macho NPT';
 const ventOption=$('outlet-end').querySelector('option[value=vent45]');
 ventOption.disabled=kind!=='pipe';
 if($('outlet-end').selectedOptions[0]?.disabled)$('outlet-end').value='welded';
 $('outlet-end').previousElementSibling.textContent=kind==='elbow'?'Conexiones del codo':kind==='tee'?('Terminación '+($('tee-entry').value==='a'?'lado B':'lado A')):'Terminación de salida principal';$('branch-end').previousElementSibling.textContent=kind==='tee'&&$('tee-entry').value==='branch'?'Terminación lado B':'Terminación de derivación de la tee';
 const viaBranch=kind==='tee'&&$('tee-entry').value==='branch';if(viaBranch){$('out-nps').value=nps;$('out-nps').disabled=true;}else $('out-nps').disabled=false;for(const option of $('tee-run-nps').options)option.disabled=Number(option.value)<nps;if(Number($('tee-run-nps').value)<nps)$('tee-run-nps').value=nps;
 $('roll').disabled=['flange','cap','elbolet'].includes(kind)||kind==='pipe'&&$('outlet-end').value!=='vent45';
 for(const option of $('out-nps').options)option.disabled=['tee','sockolet','thredolet','latrolet','elbolet','poncho'].includes(kind)&&Number(option.value)>nps;
 if(['tee','sockolet','thredolet','latrolet','elbolet','poncho'].includes(kind)&&Number($('out-nps').value)>nps)$('out-nps').value=nps;
 const spec=item(catalog,nps),f=spec.flanges[$('rating').value];$('dim-info').textContent=`DE cañería: ${spec.odMM} mm · Brida ${$('rating').value}: Ø ${f.diameterMM.toFixed(1)} mm · espesor ${f.thicknessMM.toFixed(1)} mm · ${f.boltCount} pernos.`;
 if(kind==='reducer')$('dim-info').textContent='Reducción BW '+($('reduction').value==='eccentric'?'excéntrica':'concéntrica')+' · '+item(catalog,nps).label+' × '+item(catalog,Number($('out-nps').value)).label+' · extremos para soldar. El giro orienta el lado plano de la excéntrica.';
 if(kind==='gauge')$('dim-info').textContent=p?.threadGender==='male'?'Entrada NPT hembra de '+spec.label+' · instrumento terminal.':'Selecciona un niple con salida NPT macho para conectar el manómetro.';
 if(kind==='valve'&&$('valve-connection').value==='threaded')$('dim-info').textContent='Entrada y salida NPT hembra. Para conectarlas se utiliza un niple con rosca macho; las medidas se heredan del extremo elegido.';if(['sockolet','thredolet','latrolet','elbolet','poncho'].includes(kind))$('dim-info').textContent='Principal: '+item(catalog,nps).label+' · Salida: '+item(catalog,Number($('out-nps').value)).label+' · '+(kind==='poncho'?'Poncho curvo y ramal soldado':kind==='thredolet'?'Rosca NPT':kind==='sockolet'?'Soldadura socket · SW':kind==='latrolet'?'Derivación soldada a 45°':'Derivación soldada en codo');
 $('attach').disabled=!selected||!activePort;$('apply').disabled=!selected;$('delete').disabled=!selected;
 $('add').disabled=Boolean(selected)||kind==='gauge'&&p?.threadGender!=='male'||(['sockolet','thredolet','latrolet','elbolet','poncho'].includes(kind)?!$('run-pipe').value:!activePort);
}
function form(){const source=selected?design.components.find(c=>c.id===selected):null;return {...(source||{}),padLengthMM:Number($('pad-length').value),padThicknessMM:Number($('pad-thickness').value),padCoverageDeg:Number($('pad-coverage').value),pipeXMM:Number($('pipe-x').value),pipeYMM:Number($('pipe-y').value),pipeZMM:Number($('pipe-z').value),pipeYawDeg:Number($('pipe-yaw').value),pipePitchDeg:Number($('pipe-pitch').value),pipeCurveDeg:Number($('pipe-curve').value),pipeCurveRollDeg:Number($('pipe-curve-roll').value),id:source?.id||'c'+uid().slice(0,24),...(source?.lineColor?{lineColor:source.lineColor}:{}),parentPort:['sockolet','thredolet','latrolet','elbolet','poncho'].includes(kindValue())?$('run-pipe').value+':tap':source?.parentPort||activePort,branchYawDeg:Number($('branch-yaw').value),branchPitchDeg:Number($('branch-pitch').value),branchDirection:$('olet-angle').value,tapOffsetMM:kindValue()==='elbolet'?0:Number($('tap-offset').value),teeEntry:$('tee-entry').value,teeRunNps:Number($('tee-run-nps').value),kind:kindValue(),tag:$('tag').value.trim()||nextTag(kindValue()),nps:Number($('nps').value),outNps:Number($('out-nps').value),branchNps:Number($('out-nps').value),rating:$('rating').value,outletEnd:$('outlet-end').value,branchEnd:$('branch-end').value,outletRating:$('outlet-rating').value,lengthMM:kindValue()==='gauge'?(source?.lengthMM??100):Number($('length').value),...(kindValue()==='gauge'?{gaugeDiameterMM:Number($('length').value)}:{}),radiusMM:Number($('radius').value),branchLengthMM:Number($('branch-length').value),rollDeg:Number($('roll').value),bendAngle:Number($('bend').value),reduction:$('reduction').value,inletEnd:$('inlet-end').value,valveConnection:$('valve-connection').value,valveType:$('valve-type').value};}
function componentLineRoots(){
 const roots=new Map();
 for(const component of design.components){
  const parentId=component.parentPort.split(':',1)[0];
  roots.set(component.id,roots.get(parentId)||component);
 }
 return roots;
}
function savedLineColor(root){
 const color=root?.lineColor;
 return typeof color==='string'&&/^#[0-9a-f]{6}$/i.test(color)?color:null;
}
function refreshLineColor(){
 const root=selected?componentLineRoots().get(selected):null;
 $('line-color-controls').hidden=!root;
 const color=savedLineColor(root);
 $('line-color').value=color||'#3977aa';
 $('line-color-reset').disabled=!color;
 $('line-color-help').textContent=root?'Línea desde '+root.tag+' · incluye sus derivaciones conectadas.':'';
}
function setLineColor(color){
 const root=selected?componentLineRoots().get(selected):null;
 if(!root||savedLineColor(root)===color)return;
 if(!mutate(next=>{
  const start=next.components.find(c=>c.id===root.id);
  if(color)start.lineColor=color;
  else delete start.lineColor;
 }))return;
 status(color?'Color aplicado a la línea desde '+root.tag+'.':'Colores originales restaurados en la línea desde '+root.tag+'.');
}
function refresh(){
 refreshLineColor();
 $('title').value=design.title;$('direction').value=design.direction;$('direction').disabled=design.components.length>0;$('count').textContent=design.components.length+' componentes · '+(design.repairs||[]).length+' reparaciones · '+(design.annotations||[]).length+' marcas';$('project').textContent=design.title;$('empty').hidden=design.components.length>0||(design.equipments||[]).length>0;
 $('port').replaceChildren(...result.freePorts.map(p=>new Option(p.label+(p.nps?' · '+item(catalog,p.nps).label:''),p.id)));$('port').value=activePort;
 const p=result.ports.get(activePort);$('port-info').textContent=p?`X ${p.position[0].toFixed(1)} · Y ${p.position[1].toFixed(1)} · Z ${p.position[2].toFixed(1)} mm${p.endType==='flanged'?' · Enflanchado '+p.rating:''}`:'No quedan extremos abiertos. Selecciona un elemento para modificarlo.';
 const eqid=$('equipment').value;$('equipment').replaceChildren(...(design.equipments||[]).map(e=>new Option(e.tag,e.id)));if((design.equipments||[]).some(e=>e.id===eqid))$('equipment').value=eqid;equipmentForm();
 const run=$('run-pipe').value;$('run-pipe').replaceChildren(...result.nodes.filter(n=>(n.kind==='pipe'||n.kind==='elbow')).map(n=>new Option(n.tag+' · '+item(catalog,n.nps).label+' · '+n.length.toFixed(0)+' mm',n.id)));if(result.nodes.some(n=>(n.kind==='pipe'||n.kind==='elbow')&&n.id===run))$('run-pipe').value=run;
 $('component-list').replaceChildren(...result.nodes.map(n=>new Option(n.tag+' · '+TYPES[n.kind]+(n.kind==='valve'?' '+VALVES[n.valveType]:n.kind==='reducer'?' '+(n.reduction==='eccentric'?'excéntrico':'concéntrico'):'')+' · '+item(catalog,n.nps).label,n.id)));$('component-list').value=selected||'';$('undo').disabled=$('panel-undo').disabled=!undo.length;$('redo').disabled=$('panel-redo').disabled=!redo.length;conditional();refreshContinuation();refreshDetailUI();height();
}
function continueFrom(id){if(!result.freePorts.some(p=>p.id===id)||!updateSelected())return;clearTimeout(liveTimer);liveSelection=null;activePort=id;if(selected)$('kind').value='pipe';selected=null;selectedEquipmentId=null;const parent=id.split(':')[0];continuationId=design.components.some(c=>c.id===parent)?parent:null;defaults();renderModel();refresh();status('Continúa desde '+result.ports.get(id).label+'. Elige el tipo y pulsa Agregar componente.');}
function refreshContinuation(){
 const source=[selected,continuationId].find(id=>design.components.some(c=>c.id===id)),ports=result.freePorts.filter(p=>source?p.id.startsWith(source+':'):p.id===activePort);
 $('continuation').replaceChildren(...ports.map(p=>{const button=document.createElement('button');button.type='button';button.textContent='Preparar próximo · '+p.label+' · '+(p.endType==='flanged'?'enflanchado':p.endType==='threaded'?'roscado NPT':'para soldar');button.className=p.id===activePort?'primary':'';button.onclick=()=>continueFrom(p.id);return button;}));
 const host=result.nodes.find(n=>n.id===source);if(host?.kind==='tee'){const free=new Set(result.freePorts.map(p=>p.id));$('continuation').replaceChildren(...['in','out','branch'].map(suffix=>{const id=host.id+':'+suffix,port=result.ports.get(id),entryName=host.teeEntry==='branch'?'derivación':host.teeEntry==='b'?'lado B':'lado A',button=document.createElement('button');button.textContent=(free.has(id)?(selected?'Agregar después de ':'Continuar desde '):'Ocupada: ')+(port?.label||host.tag+' · '+entryName);button.disabled=!free.has(id);button.className=id===activePort?'primary':'';button.onclick=()=>continueFrom(id);return button;}));}if(host&&(host.kind==='pipe'||host.kind==='elbow'&&host.bendAngle===90)){const button=document.createElement('button');button.textContent=host.kind==='pipe'?'Agregar derivación sobre este tramo':'Agregar derivación al centro del codo';button.onclick=()=>{selected=null;$('kind').value=host.kind==='pipe'?'sockolet':'elbolet';$('run-pipe').value=host.id;defaults();refresh();};$('continuation').append(button);if(host.kind==='pipe'){const padButton=document.createElement('button');padButton.textContent='Agregar poncho de refuerzo sobre este tramo';padButton.onclick=()=>{if(!updateSelected())return;selected=null;$('kind').value='poncho';$('run-pipe').value=host.id;defaults();refresh();};$('continuation').append(padButton);}}
 if(host?.kind==='pipe'&&!result.ports.has(host.id+':in')){const note=document.createElement('div');note.className='mode-note';note.textContent='Inicio de '+host.tag+': ocupado por '+(result.nodes.find(n=>n.id===host.parentPort.split(':')[0])?.tag||'la conexión anterior')+'. Para prolongar hacia atrás, selecciona un inicio libre.';$('continuation').prepend(note);}
 const port=result.ports.get(activePort);$('connection-help').textContent=port?.endType==='threaded'?'Salida NPT '+(port.threadGender==='male'?'macho: conecta un codo, una válvula o un manómetro de rosca hembra.':'hembra: continúa con un niple de rosca macho.'):port?'Siguiente conexión: '+port.label+'. '+(port.endType==='flanged'?'Se agrega la contraparte enflanchada al continuar con piping.':'La continuación se une por soldadura.'):'Selecciona otro extremo libre para continuar.';
 const current=result.nodes.find(n=>n.id===selected);
 $('build-mode').textContent=current?'EDITAR SELECCIONADO · '+current.tag:'CONFIGURAR PRÓXIMO COMPONENTE';$('build-mode').classList.toggle('editing',Boolean(current));$('component-heading').textContent=current?'PROPIEDADES DE '+current.tag:'PROPIEDADES DEL PRÓXIMO COMPONENTE';
 $('kind-label').textContent=current?'Tipo del componente seleccionado':'Tipo de componente nuevo';
 $('delete').textContent=current?'Eliminar '+current.tag:'Eliminar seleccionado';
 $('build-context').textContent=current?'Estás modificando '+current.tag+'. Los cambios se aplican de inmediato al componente existente. Para agregar otro, elige Inicio o Salida en Punto de conexión.':port?'Estás preparando un componente NUEVO en '+port.label+'. Los valores de abajo se usarán al pulsar Agregar. No editan el tramo anterior.':'Sin componente seleccionado. Elige un extremo libre para preparar la continuación.';
 $('add').textContent=current?'Elige una salida para continuar':['sockolet','thredolet','latrolet','elbolet','poncho'].includes(kindValue())?'+ Agregar derivación':port?'+ Agregar componente a '+port.label:'Sin extremos libres';
}
function selectNode(id){selectedRepairId=null;const selectedRun=result.nodes.find(n=>n.id===id&&n.kind==='pipe');if(selectedRun)$('repair-host').value=id;const component=design.components.find(c=>c.id===id);if(component&&isOlet(component)){$('run-pipe').value=component.parentPort.split(':')[0];$('tap-offset').value=component.tapOffsetMM;$('branch-yaw').value=component.branchYawDeg??0;$('branch-pitch').value=component.branchPitchDeg??0;$('olet-angle').value=component.branchDirection||(component.branchAngle===45?'inlet':'outlet');}continuationId=id;clearTimeout(liveTimer);liveSelection=null;selected=id;selectedEquipmentId=null;const c=design.components.find(c=>c.id===id);if(c){for(const [field,key] of [['pad-length','padLengthMM'],['pad-thickness','padThicknessMM'],['pad-coverage','padCoverageDeg'],['pipe-x','pipeXMM'],['pipe-y','pipeYMM'],['pipe-z','pipeZMM'],['pipe-yaw','pipeYawDeg'],['pipe-pitch','pipePitchDeg'],['pipe-curve','pipeCurveDeg'],['pipe-curve-roll','pipeCurveRollDeg'],['outlet-end','outletEnd'],['branch-end','branchEnd'],['tee-entry','teeEntry'],['tee-run-nps','teeRunNps'],['inlet-end','inletEnd'],['valve-connection','valveConnection'],['kind','kind'],['tag','tag'],['nps','nps'],['rating','rating'],['outlet-rating','outletRating'],['length','lengthMM'],['radius','radiusMM'],['branch-length','branchLengthMM'],['roll','rollDeg'],['bend','bendAngle'],['reduction','reduction'],['valve-type','valveType']])$(field).value=(key==='kind'&&c.kind==='reducer'?'reducer-'+c.reduction:c[key])??(key==='padLengthMM'?250:key==='padThicknessMM'?6:key==='padCoverageDeg'?160:key.startsWith('pipe')?0:key==='inletEnd'?'auto':key==='valveConnection'?'flanged':key==='teeEntry'?'a':key==='teeRunNps'?c.nps:['outletEnd','branchEnd'].includes(key)?'welded':c.rating);$('out-nps').value=c.kind==='tee'?c.branchNps:c.outNps;if(c.kind==='gauge'){const node=result.nodes.find(n=>n.id===id);$('length').value=c.gaugeDiameterMM??Number((node.length-node.odMM*.85).toFixed(3));}status('Seleccionado '+c.tag+'. Los cambios se actualizan automáticamente.');}refresh();highlight();}
const wrap=$('viewport'),scene=new THREE.Scene();scene.background=new THREE.Color('#edf3f7');
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));wrap.append(renderer.domElement);
const camera=new THREE.OrthographicCamera(-1000,1000,700,-700,.1,1e7);camera.up.set(0,0,1);camera.position.set(3000,-3000,3000);
const controls=new OrbitControls(camera,renderer.domElement);controls.mouseButtons={LEFT:THREE.MOUSE.ROTATE,MIDDLE:THREE.MOUSE.PAN,RIGHT:THREE.MOUSE.PAN};renderer.domElement.addEventListener('pointerdown',e=>{if(e.button===1)e.preventDefault();});controls.enableDamping=true;controls.dampingFactor=.08;controls.zoomSpeed=.7;controls.panSpeed=.7;controls.minZoom=.02;controls.maxZoom=80;
scene.add(new THREE.HemisphereLight(0xffffff,0x6a8193,2.4));const sun=new THREE.DirectionalLight(0xffffff,2.5);sun.position.set(3,-4,6);scene.add(sun);
const model=new THREE.Group(),portsGroup=new THREE.Group(),labelsGroup=new THREE.Group();scene.add(model,portsGroup,labelsGroup);
const pipeModel=new THREE.Group(),equipmentModel=new THREE.Group();const repairsGroup=new THREE.Group(),annotationsGroup=new THREE.Group();model.add(pipeModel,equipmentModel,repairsGroup);scene.add(annotationsGroup);
const grid=new THREE.GridHelper(10000,50,0xc9d8e2,0xdfE8ee);grid.rotation.x=Math.PI/2;grid.position.z=-1;scene.add(grid);
const axes=new THREE.AxesHelper(300);scene.add(axes);
const metal=new THREE.MeshStandardMaterial({color:0x7895a7,metalness:.6,roughness:.36,side:THREE.DoubleSide}),flangeMat=new THREE.MeshStandardMaterial({color:0xa7b9c5,metalness:.65,roughness:.3}),valveMat=new THREE.MeshStandardMaterial({color:0x168b78,metalness:.4,roughness:.37}),innerMat=new THREE.MeshStandardMaterial({color:0x415d70,roughness:.8,side:THREE.DoubleSide}),nutMat=new THREE.MeshStandardMaterial({color:0x445b6b,metalness:.65,roughness:.4});
function planeQuaternion(axis){const n=normal(axis),b=cross(axis,n);return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(new THREE.Vector3(...n),new THREE.Vector3(...b),new THREE.Vector3(...axis)));}
const repairMat=new THREE.MeshStandardMaterial({color:0xc48c32,metalness:.55,roughness:.43,side:THREE.DoubleSide});
const v=a=>new THREE.Vector3(...a),yaxis=new THREE.Vector3(0,1,0),zaxis=new THREE.Vector3(0,0,1),shared=new Set([metal,flangeMat,valveMat,innerMat,nutMat,repairMat]);
function clear(group){
 const materials=new Set();
 for(const child of [...group.children]){
  group.remove(child);
  child.traverse(object=>{
   object.geometry?.dispose();
   const list=Array.isArray(object.material)?object.material:[object.material];
   for(const material of list)if(material&&!shared.has(material))materials.add(material);
  });
 }
 for(const material of materials){material.map?.dispose();material.dispose();}
}
function mesh(geo,mat,parent=model){const m=new THREE.Mesh(geo,mat);parent.add(m);return m;}
function cylinder(a,b,r,mat=metal,parent=model,r2=r){const delta=v(sub(b,a)),m=mesh(new THREE.CylinderGeometry(r2,r,delta.length(),32,1,false),mat,parent);m.position.copy(v(mul(add(a,b),.5)));m.quaternion.setFromUnitVectors(yaxis,delta.normalize());return m;}
function tube(a,b,od,parent,mat=metal){const axis=norm(sub(b,a)),len=Math.hypot(...sub(b,a)),r=od/2,inside=r*.86;
 for(const [radius,material] of [[r,mat],[inside,innerMat]]){const m=mesh(new THREE.CylinderGeometry(radius,radius,len,36,1,true),material,parent);m.position.copy(v(mul(add(a,b),.5)));m.quaternion.setFromUnitVectors(yaxis,v(axis));}
 for(const p of [a,b]){const m=mesh(new THREE.RingGeometry(inside,r,36),mat,parent);m.position.copy(v(p));m.quaternion.setFromUnitVectors(zaxis,v(axis));}
}
function drawCurvedPipe(n,group){
 const positions=[],indices=[],steps=96,sides=48,r=n.odMM/2;
 for(const radius of [r,r*.86])for(let j=0;j<=steps;j++)for(let k=0;k<=sides;k++){
  const angle=k*2*Math.PI/sides,f=pipeFrame(n,n.length*j/steps),offset=radius*Math.cos(angle),cut=n.endType==='vent45'?offset*(j/steps)**8:0;
  positions.push(...add(add(f.point,mul(f.axis,cut)),add(mul(f.normal,offset),mul(f.binormal,radius*Math.sin(angle)))));
 }
 const ring=sides+1,layer=(steps+1)*ring;
 for(let side=0;side<2;side++)for(let j=0;j<steps;j++)for(let k=0;k<sides;k++){const a=side*layer+j*ring+k,b=a+ring;if(side)indices.push(a,b,a+1,a+1,b,b+1);else indices.push(a,a+1,b,a+1,b+1,b);}
 for(const j of [0,steps])for(let k=0;k<sides;k++){const a=j*ring+k,b=layer+a;indices.push(a,b,a+1,a+1,b,b+1);}
 const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.setIndex(indices);geometry.computeVertexNormals();const body=mesh(geometry,metal,group);body.name='Tubo curvado continuo';
}
function drawVentNipple(n,group){
 const radius=n.odMM/2,segments=48,positions=[],indices=[];
 const side=cross(n.axis,n.normal);
 for(const [r,atOutlet] of [[radius,false],[radius,true],[radius*.86,true],[radius*.86,false]]){
  for(let i=0;i<=segments;i++){
   const angle=i*2*Math.PI/segments;
   const offset=r*Math.cos(angle);
   const radial=add(mul(n.normal,offset),mul(side,r*Math.sin(angle)));
   const center=atOutlet?add(n.end,mul(n.axis,offset)):n.start;
   positions.push(...add(center,radial));
  }
 }
 for(let ring=0;ring<4;ring++){
  for(let i=0;i<segments;i++){
   const a=ring*(segments+1)+i,b=((ring+1)%4)*(segments+1)+i;
   indices.push(a,a+1,b,a+1,b+1,b);
  }
 }
 const geometry=new THREE.BufferGeometry();
 geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
 geometry.setIndex(indices);
 geometry.computeVertexNormals();
 mesh(geometry,metal,group).name='Niple de venteo abierto · corte a 45°';
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
function reducer(n,parent){
 const outDiameter=item(catalog,n.outNps).odMM,u=n.normal,b=cross(n.axis,u),positions=[],indices=[],steps=48,sides=64,ring=sides+1,layer=(steps+1)*ring;
 for(const inside of [false,true])for(let j=0;j<=steps;j++){const f=reducerSection(n,outDiameter,j/steps),r=f.radius*(inside?.86:1);for(let k=0;k<=sides;k++){const a=k*2*Math.PI/sides;positions.push(...add(f.center,add(mul(u,Math.cos(a)*r),mul(b,Math.sin(a)*r))));}}
 for(let side=0;side<2;side++)for(let j=0;j<steps;j++)for(let k=0;k<sides;k++){const a=side*layer+j*ring+k,c=a+ring;if(side)indices.push(a,c,a+1,a+1,c,c+1);else indices.push(a,a+1,c,a+1,c+1,c);}
 for(const j of [0,steps])for(let k=0;k<sides;k++){const a=j*ring+k,c=layer+a;indices.push(a,c,a+1,a+1,c,c+1);}
 const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geo.setIndex(indices);geo.computeVertexNormals();const body=mesh(geo,metal,parent);body.name=n.reduction==='eccentric'?'Reducción excéntrica BW':'Reducción concéntrica BW';
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
function selectEquipment(id){if(!id)return;selectedRepairId=null;selected=null;selectedEquipmentId=id;$('equipment').value=id;equipmentForm();highlight();status('Equipo '+(design.equipments||[]).find(e=>e.id===id).tag+' seleccionado. Puedes moverlo aquí o abrir Editar equipo.');}
function syncEquipmentModels(){
 for(const group of [...equipmentModel.children]){const e=(design.equipments||[]).find(e=>e.id===group.userData.equipmentId);if(!e||group.userData.assetKey!==equipmentKey(e)){equipmentModel.remove(group);clear(group);}}
 for(const e of design.equipments||[]){let group=equipmentModel.children.find(g=>g.userData.equipmentId===e.id);if(!group){group=new THREE.Group();group.add(loadAsset(e.asset));group.userData={equipmentId:e.id,assetKey:equipmentKey(e)};addNameplate(group,e);equipmentModel.add(group);}group.position.set(...e.position);group.rotation.z=e.rotationDeg*Math.PI/180;}
}
function drawBallValve(n,f,finish,group){
 const od=n.odMM,axis=n.axis,up=n.normal,side=norm(cross(axis,up));
 const cast=new THREE.MeshStandardMaterial({color:0x9ca5ab,metalness:.56,roughness:.48,side:THREE.DoubleSide});
 const blue=new THREE.MeshStandardMaterial({color:0x1766be,metalness:.24,roughness:.39});
 const seat=add(n.start,mul(axis,f.lengthMM));
 const halfRun=Math.hypot(...sub(finish,seat))/2;
 tube(seat,finish,od,group,cast);
 const body=mesh(new THREE.SphereGeometry(1,40,28),cast,group);
 body.name='Cuerpo fundido de válvula de bola';
 body.position.copy(v(n.center));
 const basis=new THREE.Matrix4().makeBasis(v(axis),v(up),v(side));
 body.quaternion.setFromRotationMatrix(basis);
 body.scale.set(Math.min(od*1.18,halfRun*.94),od*.87,od*.83);
 const joint=add(n.center,mul(axis,Math.min(od*.48,halfRun*.36)));
 const jointFace=offset=>add(joint,mul(axis,od*offset));
 cylinder(jointFace(-.14),jointFace(-.015),od*.86,cast,group).name='Unión del cuerpo partido';
 cylinder(jointFace(-.015),jointFace(.015),od*.843,nutMat,group).name='Junta del cuerpo';
 cylinder(jointFace(.015),jointFace(.14),od*.86,cast,group).name='Tapa apernada del cuerpo';
 for(let i=0;i<4;i++){
  const angle=(i+.5)*Math.PI/2;
  const radial=add(mul(up,Math.cos(angle)),mul(side,Math.sin(angle)));
  const offset=mul(radial,od*.82);
  cylinder(add(jointFace(-.14),offset),add(jointFace(.14),offset),od*.20,cast,group);
  const bolt=mesh(new THREE.CylinderGeometry(od*.11,od*.11,od*.12,6),nutMat,group);
  bolt.position.copy(v(add(jointFace(.19),offset)));
  bolt.quaternion.setFromUnitVectors(yaxis,v(axis));
  bolt.name='Perno de la unión del cuerpo';
 }
 const at=h=>add(n.center,mul(up,h*od));
 cylinder(at(.68),at(1.14),od*.35,cast,group,od*.30).name='Cuello de válvula de bola';
 cylinder(at(1.14),at(1.31),od*.42,cast,group).name='Brida del prensaestopas';
 cylinder(at(1.31),at(1.66),od*.24,flangeMat,group).name='Prensaestopas';
 for(const sign of [-1,1]){
  const offset=mul(side,od*.32*sign);
  cylinder(add(at(1.28),offset),add(at(1.69),offset),od*.052,nutMat,group).name='Espárrago del prensaestopas';
 }
 cylinder(at(1.62),at(2.35),od*.115,flangeMat,group).name='Vástago largo de válvula de bola';
 cylinder(at(2.10),at(2.31),od*.29,blue,group).name='Cubo de la manilla';
 const lever=new THREE.Shape();
 lever.moveTo(0,0);
 lever.lineTo(od*.82,0);
 lever.lineTo(od*1.60,od*.40);
 lever.lineTo(od*3.75,od*.40);
 lever.quadraticCurveTo(od*3.89,od*.40,od*3.89,od*.48);
 lever.quadraticCurveTo(od*3.89,od*.56,od*3.75,od*.56);
 lever.lineTo(od*1.56,od*.56);
 lever.lineTo(od*.78,od*.16);
 lever.lineTo(0,od*.16);
 lever.closePath();
 const geometry=new THREE.ExtrudeGeometry(lever,{depth:od*.25,bevelEnabled:false,curveSegments:8});
 geometry.translate(0,0,-od*.125);
 const handle=mesh(geometry,blue,group);
 handle.position.copy(v(at(2.14)));
 handle.quaternion.setFromRotationMatrix(basis);
 handle.name='Manilla azul de válvula de bola';
}
function threadDepth(od){return Math.min(25,Math.max(8,od*.3));}
function drawThread(point,axis,od,parent,female=false,socketMaterial=valveMat){
 const length=threadDepth(od),radial=normal(axis),side=cross(axis,radial);
 if(female){const profile=[[od*.48,0],[od*.70,0],[od*.70,length],[od*.48,length],[od*.48,0]].map(([r,y])=>new THREE.Vector2(r,y));const socket=mesh(new THREE.LatheGeometry(profile,48),socketMaterial,parent);socket.position.copy(v(point));socket.quaternion.setFromUnitVectors(yaxis,v(axis));socket.name='Conexión hembra NPT';}
 const curve=new THREE.Curve();curve.getPoint=t=>v(add(add(point,mul(axis,t*length)),add(mul(radial,Math.cos(t*Math.PI*12)*od*(female?.485:.505)),mul(side,Math.sin(t*Math.PI*12)*od*(female?.485:.505)))));const thread=mesh(new THREE.TubeGeometry(curve,96,Math.max(.55,od*.012),6,false),nutMat,parent);thread.name=female?'Rosca hembra NPT':'Rosca macho NPT';
}
function drawThreadedRV(n,group){
 const od=n.odMM,outOD=item(catalog,n.endNps).odMM;
 const castMat=new THREE.MeshStandardMaterial({color:0x52595c,metalness:.52,roughness:.65});
 const sealMat=new THREE.MeshStandardMaterial({color:0xc54427,roughness:.58});
 const atHeight=h=>add(n.start,mul(n.axis,h));
 const bodyStart=threadDepth(od),shoulder=n.length*.53,collarTop=n.length*.58;
 const outline=[[0,bodyStart],[od*.68,bodyStart],[od*.85,bodyStart+od*.18],
  [od*.94,bodyStart+od*.42],[od*.94,shoulder-od*.28],[od*.9,shoulder-od*.12],
  [od*.77,shoulder],[od*.60,shoulder+od*.08],[0,shoulder+od*.08]];
 const body=mesh(new THREE.LatheGeometry(outline.map(([r,h])=>new THREE.Vector2(r,h)),48),castMat,group);
 body.name='Cuerpo fundido RV';
 body.position.copy(v(n.start));
 body.quaternion.setFromUnitVectors(yaxis,v(n.axis));

 function hexSection(bottom,top,bottomRadius,topRadius,name){
  const part=mesh(new THREE.CylinderGeometry(topRadius,bottomRadius,top-bottom,6),castMat,group);
  part.position.copy(v(atHeight((bottom+top)/2)));
  part.quaternion.copy(body.quaternion);
  part.name=name;
 }
 hexSection(shoulder,collarTop,od*.64,od*.64,'Contratuerca hexagonal RV');
 hexSection(collarTop,n.length-od*.10,od*.59,od*.59,'Tapa hexagonal RV');
 hexSection(n.length-od*.10,n.length,od*.59,od*.52,'Bisel de la tapa RV');

 const outletSocketBack=sub(n.end,mul(n.endAxis,threadDepth(outOD)));
 const outletRoot=add(n.center,mul(n.endAxis,Math.min(od*.60,Math.hypot(...sub(outletSocketBack,n.center))*.7)));
 cylinder(outletRoot,outletSocketBack,outOD*.76,castMat,group,outOD*.70).name='Cuello de salida lateral RV';
 drawThread(n.start,n.axis,od,group,true);
 drawThread(n.end,mul(n.endAxis,-1),outOD,group,true);

 const front=norm(cross(n.axis,n.endAxis));
 const plugCenter=add(atHeight(bodyStart+od*.55),mul(front,od*.92));
 const plugRing=mesh(new THREE.TorusGeometry(od*.19,od*.044,8,32),castMat,group);
 plugRing.name='Alojamiento del tapón frontal RV';
 plugRing.position.copy(v(plugCenter));
 plugRing.quaternion.setFromUnitVectors(zaxis,v(front));
 const recess=mesh(new THREE.CircleGeometry(od*.13,6),nutMat,group);
 recess.name='Hueco hexagonal del tapón RV';
 recess.position.copy(v(add(plugCenter,mul(front,od*.015))));
 recess.quaternion.copy(plugRing.quaternion);

 const wireCenter=atHeight(collarTop-od*.07);
 const wire=mesh(new THREE.TorusGeometry(od*.59,od*.016,8,48),nutMat,group);
 wire.name='Alambre de precinto RV';
 wire.position.copy(v(wireCenter));
 wire.quaternion.setFromUnitVectors(zaxis,v(n.axis));
 const sealStart=add(wireCenter,mul(n.endAxis,od*.56));
 const sealEnd=add(add(sealStart,mul(n.endAxis,od*.43)),mul(n.axis,-od*.73));
 cylinder(sealStart,sealEnd,od*.017,nutMat,group);
 const seal=mesh(new THREE.BoxGeometry(od*.16,od*.53,od*.08),sealMat,group);
 seal.name='Precinto RV';
 seal.position.copy(v(sealEnd));
 seal.quaternion.setFromUnitVectors(yaxis,v(norm(sub(sealEnd,sealStart))));
}
function drawFlangedGate(n,f,finish,group){
 const od=n.odMM,up=n.normal,side=norm(cross(n.axis,up));
 const seat=add(n.start,mul(n.axis,f.lengthMM));
 const cast=new THREE.MeshStandardMaterial({color:0xadb2b6,metalness:.58,roughness:.48,side:THREE.DoubleSide});
 const machined=new THREE.MeshStandardMaterial({color:0xc5cbd0,metalness:.67,roughness:.29});
 const at=h=>add(n.center,mul(up,h*od));
 tube(seat,finish,od,group,cast);
 const profile=[[0,-.79],[.32,-.77],[.56,-.63],[.72,-.38],[.78,-.03],[.73,.28],[.60,.51],[.58,.66],[0,.66]];
 const body=mesh(new THREE.LatheGeometry(profile.map(([r,h])=>new THREE.Vector2(r*od,h*od)),48),cast,group);
 body.name='Cuerpo de fundición de la compuerta';
 body.position.copy(v(n.center));
 body.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(v(n.axis),v(up),v(side)));
 const halfRun=Math.hypot(...sub(finish,seat))/2;
 body.scale.x=Math.min(1,halfRun/(od*.82));
 cylinder(at(.60),at(.86),od*.84,cast,group).name='Brida del cuerpo';
 cylinder(at(.86),at(.89),od*.824,nutMat,group).name='Junta cuerpo–bonete';
 cylinder(at(.89),at(1.12),od*.84,machined,group).name='Brida del bonete';
 cylinder(at(1.12),at(1.37),od*.60,cast,group,od*.37).name='Bonete de fundición';
 for(let i=0;i<8;i++){
  const angle=(i+.5)*Math.PI/4;
  const offset=add(mul(n.axis,Math.cos(angle)*od*.70),mul(side,Math.sin(angle)*od*.70));
  const boltAt=h=>add(at(h),offset);
  cylinder(boltAt(.49),boltAt(1.28),od*.042,machined,group).name='Espárrago del bonete';
  for(const h of [.55,1.19]){
   const nut=mesh(new THREE.CylinderGeometry(od*.083,od*.083,od*.12,6),machined,group);
   nut.position.copy(v(boltAt(h)));
   nut.quaternion.setFromUnitVectors(yaxis,v(up));
   nut.name='Tuerca hexagonal del bonete';
  }
 }
 cylinder(at(1.29),at(1.52),od*.31,cast,group).name='Alojamiento del prensaestopas';
 cylinder(at(1.51),at(1.67),od*.27,machined,group).name='Prensaestopas';
 for(const sign of [-1,1]){
  const point=(height,offset)=>v(add(at(height),mul(side,sign*offset*od)));
  const curve=new THREE.CatmullRomCurve3([point(1.24,.32),point(1.58,.43),point(2.00,.41),point(2.39,.27)]);
  mesh(new THREE.TubeGeometry(curve,24,od*.125,12,false),cast,group).name='Puente curvo del vástago';
 }
 cylinder(at(2.30),at(2.52),od*.29,cast,group).name='Cabezal del puente';
 cylinder(at(1.49),at(2.93),od*.072,machined,group).name='Vástago ascendente';
 const wheelCenter=at(2.69);
 const wheel=mesh(new THREE.TorusGeometry(od*.87,od*.051,12,64),machined,group);
 wheel.name='Volante metálico de tres radios';
 wheel.position.copy(v(wheelCenter));
 wheel.quaternion.setFromUnitVectors(zaxis,v(up));
 cylinder(at(2.53),at(2.79),od*.18,machined,group).name='Cubo del volante';
 for(let i=0;i<3;i++){
  const angle=i*2*Math.PI/3;
  const radial=add(mul(n.axis,Math.cos(angle)),mul(side,Math.sin(angle)));
  cylinder(add(at(2.58),mul(radial,od*.11)),add(wheelCenter,mul(radial,od*.86)),od*.050,machined,group);
 }
}
function drawPressureGauge(n,group){
 const od=n.odMM,radius=(n.length-od*.85)/2,face=n.normal;
 const steel=new THREE.MeshStandardMaterial({color:0xbabfc4,metalness:.62,roughness:.33});
 const depth=radius*.39;
 const back=sub(n.center,mul(face,depth*.58));
 const front=add(n.center,mul(face,depth*.42));
 const neckBase=add(n.start,mul(n.axis,threadDepth(od)));
 const neckTop=sub(n.center,mul(n.axis,radius*.87));
 cylinder(neckBase,neckTop,od*.61,steel,group,od*.46).name='Cuello del manómetro';
 drawThread(n.start,n.axis,od,group,true,steel);
 cylinder(back,front,radius,steel,group).name='Carcasa del manómetro';
 const rim=mesh(new THREE.TorusGeometry(radius*.935,radius*.056,12,64),steel,group);
 rim.position.copy(v(front));
 rim.quaternion.setFromUnitVectors(zaxis,v(face));
 rim.name='Bisel del manómetro';
 const dialCanvas=document.createElement('canvas');
 dialCanvas.width=dialCanvas.height=256;
 const ctx=dialCanvas.getContext('2d');
 ctx.fillStyle='#f5f8f9';
 ctx.fillRect(0,0,256,256);
 ctx.strokeStyle='#203342';
 ctx.fillStyle='#203342';
 ctx.textAlign='center';
 ctx.textBaseline='middle';
 ctx.font='bold 18px sans-serif';
 for(let tick=0;tick<=50;tick++){
  const angle=(135+270*tick/50)*Math.PI/180;
  const major=tick%10===0,length=major?82:92;
  const x=Math.cos(angle),y=Math.sin(angle);
  ctx.lineWidth=major?3:1.5;
  ctx.beginPath();ctx.moveTo(128+x*length,128+y*length);ctx.lineTo(128+x*104,128+y*104);ctx.stroke();
  if(major)ctx.fillText(String(tick/5),128+x*68,128+y*68);
 }
 ctx.lineWidth=4;
 ctx.beginPath();ctx.moveTo(146,110);ctx.lineTo(65,190);ctx.stroke();
 ctx.beginPath();ctx.arc(128,128,7,0,2*Math.PI);ctx.fill();
 ctx.font='bold 15px sans-serif';ctx.fillText('bar',128,192);
 const texture=new THREE.CanvasTexture(dialCanvas);
 texture.colorSpace=THREE.SRGBColorSpace;
 const dial=mesh(new THREE.CircleGeometry(radius*.90,64),new THREE.MeshBasicMaterial({map:texture}),group);
 dial.name='Carátula analógica del manómetro';
 dial.position.copy(v(add(front,mul(face,radius*.009))));
 dial.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(v(norm(cross(n.axis,face))),v(n.axis),v(face)));
}
function drawFlangedPSV(n,inletFlange,finish,group){
 const od=n.odMM,axis=n.axis,outlet=n.endAxis,side=norm(cross(axis,outlet));
 const cast=new THREE.MeshStandardMaterial({color:0x66737b,metalness:.40,roughness:.62,side:THREE.DoubleSide});
 const sealMaterial=new THREE.MeshStandardMaterial({color:0xb9472c,roughness:.62});
 const at=h=>add(n.start,mul(axis,h));
 const centerHeight=dot(sub(n.center,n.start),axis);
 const available=n.length-centerHeight;
 const base=centerHeight+available*.24;
 const shoulder=centerHeight+available*.60;
 const plateDepth=Math.min(od*.17,available*.075);
 const boltHeight=Math.min(od*.095,plateDepth*.75);
 const jointRotation=new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(v(outlet),v(side),v(axis)));
 const inletSeat=at(inletFlange.lengthMM);
 const outOD=item(catalog,n.endNps).odMM;
 tube(inletSeat,n.center,od,group,cast);
 tube(n.center,finish,outOD,group,cast);
 const body=mesh(new THREE.SphereGeometry(1,40,28),cast,group);
 body.name='Cuerpo fundido en ángulo de la PSV';
 body.position.copy(v(n.center));
 body.quaternion.copy(jointRotation);
 body.scale.set(od*.96,od*.89,Math.min(od*.94,available*.24));
 cylinder(n.center,at(base),od*.75,cast,group,od*.72).name='Cuello del cuerpo PSV';
 function plateAt(height,radius,depth,material,name){
  const corner=radius*.18;
  const outline=new THREE.Shape();
  const points=[[-radius+corner,-radius],[radius-corner,-radius],[radius,-radius+corner],[radius,radius-corner],[radius-corner,radius],[-radius+corner,radius],[-radius,radius-corner],[-radius,-radius+corner]];
  outline.moveTo(...points[0]);
  for(const point of points.slice(1))outline.lineTo(...point);
  outline.closePath();
  const geometry=new THREE.ExtrudeGeometry(outline,{depth,bevelEnabled:false});
  const part=mesh(geometry,material,group);
  part.position.copy(v(at(height)));
  part.quaternion.copy(jointRotation);
  part.name=name;
 }
 const jointRadius=od*.87;
 plateAt(base-plateDepth,jointRadius,plateDepth,cast,'Unión inferior del cuerpo PSV');
 plateAt(base,jointRadius,plateDepth*.12,nutMat,'Junta cuerpo–bonete PSV');
 plateAt(base+plateDepth*.12,jointRadius,plateDepth,cast,'Base del bonete PSV');
 cylinder(at(base+plateDepth),at(shoulder),od*.62,cast,group,od*.59).name='Bonete cerrado de la PSV';
 plateAt(shoulder,od*.81,plateDepth,cast,'Placa superior apernada PSV');
 for(const [height,offset] of [[base+plateDepth*1.12,od*.64],[shoulder+plateDepth,od*.60]]){
  for(const x of [-1,1])for(const y of [-1,1]){
   const point=add(add(at(height+boltHeight/2),mul(outlet,x*offset)),mul(side,y*offset));
   const bolt=mesh(new THREE.CylinderGeometry(od*.078,od*.078,boltHeight,6),flangeMat,group);
   bolt.position.copy(v(point));
   bolt.quaternion.setFromUnitVectors(yaxis,v(axis));
   bolt.name='Perno hexagonal del bonete PSV';
  }
 }
 const capBase=shoulder+plateDepth;
 const capRadius=od*.43,capHeight=n.length-capBase;
 const crown=Math.min(capRadius*.55,capHeight*.25);
 const capProfile=[[0,0],[capRadius,0],[capRadius,capHeight-crown],[capRadius*.94,capHeight-crown*.50],[capRadius*.73,capHeight-crown*.18],[capRadius*.35,capHeight],[0,capHeight]];
 const cover=mesh(new THREE.LatheGeometry(capProfile.map(([r,h])=>new THREE.Vector2(r,h)),48),cast,group);
 cover.position.copy(v(at(capBase)));
 cover.quaternion.setFromUnitVectors(yaxis,v(axis));
 cover.name='Tapa cilíndrica cerrada PSV';
 const eye=add(at(shoulder+plateDepth*.50),mul(outlet,-od*.84));
 const sealEnd=add(add(eye,mul(outlet,-od*.31)),mul(axis,-od*.29));
 cylinder(eye,sealEnd,od*.018,nutMat,group).name='Alambre del precinto PSV';
 const seal=mesh(new THREE.BoxGeometry(od*.10,od*.42,od*.065),sealMaterial,group);
 seal.position.copy(v(sealEnd));
 seal.quaternion.setFromUnitVectors(yaxis,v(norm(sub(sealEnd,eye))));
 seal.name='Precinto de seguridad PSV';
}
function drawValve(n,f,group){
 if(n.valveType==='rv'&&n.valveConnection==='threaded'){drawThreadedRV(n,group);return;}
 const threaded=n.valveConnection==='threaded';if(threaded)f={...f,lengthMM:n.odMM*.4};
 if(threaded)drawThread(n.start,n.axis,n.odMM,group,true);else drawFlange(add(n.start,mul(n.axis,f.lengthMM)),mul(n.axis,-1),f,group);
 const out=threaded?{...f,lengthMM:item(catalog,n.endNps).odMM*.4}:isRelief(n)?{...n.outletFlange,rating:n.endRating}:f,finish=sub(n.end,mul(n.endAxis,out.lengthMM));if(threaded)drawThread(n.end,mul(n.endAxis,-1),item(catalog,n.endNps).odMM,group,true);else drawFlange(finish,n.endAxis,out,group);
 if(n.valveType==='psv'&&!threaded){drawFlangedPSV(n,f,finish,group);return;}
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
 if(!threaded&&n.valveType==='gate'){drawFlangedGate(n,f,finish,group);return;}
 if(n.valveType==='ball'){drawBallValve(n,f,finish,group);return;}
 tube(add(n.start,mul(n.axis,f.lengthMM)),finish,n.odMM,group,valveMat);
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
function colorPipeGroup(group,color){
 const variants=new Map();
 group.traverse(object=>{
  const material=object.material;
  if(!object.isMesh||!material?.color||material.map)return;
  if(!shared.has(material)){material.color.set(color);return;}
  if(!variants.has(material)){
   const tinted=material.clone();
   tinted.color.set(color);
   variants.set(material,tinted);
  }
  object.material=variants.get(material);
 });
}
function renderModel(){
 const lineRoots=componentLineRoots();
 clear(pipeModel);clear(repairsGroup);clear(annotationsGroup);clear(portsGroup);clear(labelsGroup);syncEquipmentModels();
 for(const n of result.nodes){const group=new THREE.Group();group.userData.id=n.id;pipeModel.add(group);const f={...n.flange,rating:n.rating};
  if(n.outletEndFlange)drawFlange(n.end,n.endAxis,{...n.outletEndFlange,rating:n.rating},group);
  if(n.branch?.flangeSpec)drawFlange(n.branch.bodyPosition,n.branch.axis,{...n.branch.flangeSpec,rating:n.rating},group);
  if(n.adapter)drawFlange(n.adapter.start,n.adapter.axis,f,group);
  if(n.origin.id!=='origin'&&n.origin.endType==='plain'&&!n.hideInletWeld){const weld=mesh(new THREE.TorusGeometry(item(catalog,n.origin.nps??n.nps).odMM/2,Math.max(1.3,n.odMM*.018),8,40),nutMat,group);weld.name='Cordón de soldadura';if(n.weldTag)weld.userData.weldComponentId=n.id;weld.position.copy(v(n.origin.position));weld.quaternion.setFromUnitVectors(zaxis,v(n.axis));}
  if(n.origin.endType==='flanged'){bolts(add(n.origin.position,mul(n.axis,1.5)),n.axis,f,group);}else if(n.adapter&&!n.adapter.reverse){bolts(add(n.adapter.start,mul(n.axis,f.lengthMM+1.5)),n.axis,f,group);}
  if(n.kind==='elbolet')drawElbolet(n,group);
  else if(n.kind==='poncho')drawPonchoGeometry(n,group,metal,nutMat);
  else if(isOlet(n)){const od=item(catalog,n.outNps).odMM;const neck=add(n.start,mul(n.axis,n.length*.65));cylinder(n.start,neck,od*.88,metal,group,od*.57);tube(neck,n.end,od,group);if(n.kind==='thredolet'){for(let i=0;i<5;i++){const thread=mesh(new THREE.TorusGeometry(od*.43,Math.max(.8,od*.012),6,32),nutMat,group);thread.name='Rosca NPT thredolet';thread.position.copy(v(sub(n.end,mul(n.axis,2+i*2))));thread.quaternion.setFromUnitVectors(zaxis,v(n.axis));}}const weld=mesh(new THREE.TorusGeometry(od*.85,Math.max(2,od*.055),10,40),nutMat,group);weld.name='Soldadura sockolet a línea principal';weld.position.copy(v(n.start));weld.quaternion.setFromUnitVectors(zaxis,v(n.axis));}
  else if(n.kind==='pipe'){if(n.endType==='vent45'&&!n.pipeCurveDeg)drawVentNipple(n,group);else if(n.pipeCurveDeg)drawCurvedPipe(n,group);else tube(n.start,n.end,n.odMM,group);if(n.inletType==='threaded')drawThread(n.start,n.axis,n.odMM,group);if(n.endType==='threaded')drawThread(n.end,mul(n.endAxis,-1),n.odMM,group);}
  else if(n.kind==='elbow'){const R=Math.max(n.radiusMM,n.odMM*.6),angle=n.bendAngle*Math.PI/180,path=new THREE.Curve();path.getPoint=t=>v(add(n.start,add(mul(n.axis,R*Math.sin(angle*t)),mul(n.normal,R*(1-Math.cos(angle*t))))));mesh(openElboletBores(new THREE.TubeGeometry(path,96,n.odMM/2,64,false),n),metal,group);if(n.endType==='threaded'){drawThread(n.start,n.axis,n.odMM,group,true);drawThread(n.end,mul(n.endAxis,-1),n.odMM,group,true);}}
  else if(n.kind==='tee'){tube(n.teeA,n.teeB,n.odMM,group);tube(n.center,n.teeLegEnd,item(catalog,n.branchNps).odMM,group);}
  else if(n.kind==='reducer')reducer(n,group);
  else if(n.kind==='flange')drawFlange(n.reverse?n.end:n.start,n.reverse?mul(n.axis,-1):n.axis,f,group);
  else if(n.kind==='cap')plate(n.start,n.axis,f,group,true);
  else if(n.kind==='gauge')drawPressureGauge(n,group);
  else if(n.kind==='valve')drawValve(n,f,group);
  const color=savedLineColor(lineRoots.get(n.id));
  if(color)colorPipeGroup(group,color);
 }
 drawRepairs(repairsGroup,design,result,repairMat,nutMat);createAnnotations(annotationsGroup,design);
 const box=new THREE.Box3().setFromObject(model);totalSize=box.isEmpty()?1500:Math.max(box.getSize(new THREE.Vector3()).length(),500);grid.position.z=box.isEmpty()?-1:box.min.z-40;
 for(const repair of design.repairs||[]){const node=result.nodes.find(n=>n.id===repair.hostId),frame=pipeFrame(node,repair.startMM+repair.lengthMM/2),point=add(frame.point,mul(normal(frame.axis,repair.rollDeg),node.odMM/2+repair.thicknessMM+totalSize*.025));label(repair.tag,point);}
 for(const e of design.equipments||[]){const group=equipmentModel.children.find(g=>g.userData.equipmentId===e.id),box=new THREE.Box3().setFromObject(group),center=box.getCenter(new THREE.Vector3());label(e.tag,[center.x,center.y,box.max.z+totalSize*.04]);}
 for(const n of result.nodes){if(n.weldTag)label(n.weldTag,add(n.start,mul(normal(n.axis),Math.max(n.odMM,totalSize*.04))));const shift=Math.max(n.odMM*(n.kind==='valve'?3.3:1.3),totalSize*.06),point=add(n.center,mul(n.normal,shift));const sprite=label(n.tag+(n.kind==='pipe'?' · '+n.length.toFixed(0)+' mm':''),point);const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints([v(n.center),v(point)]),new THREE.LineBasicMaterial({color:0x607e90,transparent:true,opacity:.8,depthTest:false}));sprite.userData.line=line;sprite.userData.center=[...n.center];labelsGroup.add(line);}
 for(const p of result.freePorts){if(p.id!=='origin')label(p.label,add(p.position,mul(normal(p.axis),Math.max(80,totalSize*.035))));const r=Math.max(8,Math.min(40,totalSize*.012)),m=mesh(new THREE.SphereGeometry(r,20,16),new THREE.MeshStandardMaterial({color:p.id===activePort?0xf7a73b:0x20b99d,emissive:p.id===activePort?0x422200:0x003329}),portsGroup);m.position.copy(v(p.position));m.userData.portId=p.id;}
 labelsGroup.visible=labelsVisible;grid.scale.setScalar(Math.max(1,totalSize/6000));axes.scale.setScalar(Math.max(1,totalSize/2000));highlight();
}
function highlight(){model.traverse(o=>{if(o.isMesh&&o.material){const id=o.parent?.userData.id;/* Materiales compartidos se mantienen neutros; la selección usa un recuadro. */}});const old=scene.getObjectByName('selection-box');if(old){scene.remove(old);old.geometry.dispose();old.material.dispose();}if(selected||selectedEquipmentId||selectedRepairId){const group=selected?pipeModel.children.find(g=>g.userData.id===selected):selectedEquipmentId?equipmentModel.children.find(g=>g.userData.equipmentId===selectedEquipmentId):repairsGroup.children.find(g=>g.userData.repairId===selectedRepairId);if(group){const box=new THREE.BoxHelper(group,0x0c9b87);box.name='selection-box';scene.add(box);}}}
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
function resize(){
 const width=wrap.clientWidth||800,heightPx=wrap.clientHeight||650;
 renderer.setSize(width,heightPx,false);
 const halfWidth=(camera.top-camera.bottom)/2*width/heightPx;
 camera.left=-halfWidth;
 camera.right=halfWidth;
 camera.updateProjectionMatrix();
 height();
}
new ResizeObserver(resize).observe(wrap);$('panel').addEventListener('toggle',()=>{setTimeout(resize,50);height();});
const canvas=renderer.domElement;
const pickRay=new THREE.Raycaster(),pickPointer=new THREE.Vector2();
let clickStart=null;
canvas.addEventListener('pointerdown',event=>{
 clickStart=event.isPrimary&&event.button===0?{id:event.pointerId,x:event.clientX,y:event.clientY}:null;
});
canvas.addEventListener('pointermove',event=>{
 if(clickStart?.id===event.pointerId&&Math.hypot(event.clientX-clickStart.x,event.clientY-clickStart.y)>4)clickStart=null;
});
canvas.addEventListener('pointercancel',()=>{clickStart=null;});
canvas.addEventListener('pointerup',event=>{
 const start=clickStart;
 clickStart=null;
 if(!start||start.id!==event.pointerId||event.button!==0||Math.hypot(event.clientX-start.x,event.clientY-start.y)>4)return;
 const rect=canvas.getBoundingClientRect();
 if(!rect.width||!rect.height)return;
 const x=event.clientX-rect.left,y=event.clientY-rect.top;
 if(x<0||y<0||x>=rect.width||y>=rect.height)return;
 camera.updateMatrixWorld();
 model.updateMatrixWorld(true);
 portsGroup.updateMatrixWorld(true);
 if(weldMode){pickPointer.set(x/rect.width*2-1,1-y/rect.height*2);pickRay.setFromCamera(pickPointer,camera);const hits=pickRay.intersectObject(pipeModel,true);let chosen=null;for(const h of hits){let g=h.object;while(g&&!g.userData.id)g=g.parent;const n=result.nodes.find(n=>n.id===g?.userData.id);if(n?.kind==='pipe'){chosen={node:n,point:h.point.toArray()};break;}}if(!chosen){status('Haz clic sobre la superficie de un tramo de tubo.',true);return;}try{if(!updateSelected())return;const output=splitPipe(design,chosen.node.id,pipeDistance(chosen.node,chosen.point),catalog,'c'+uid().slice(0,24));selected=null;setDesign(output.design);selectNode(output.newId);setWeldMode(false);status('Soldadura '+output.weldTag+' creada. Segmentos identificados; conexiones conservadas.');}catch(error){status(error.message,true);}return;}
 if(marking){pickPointer.set(x/rect.width*2-1,1-y/rect.height*2);pickRay.setFromCamera(pickPointer,camera);placeAnnotation(pickRay);return;}
 function hitAt(px,py,includePorts){
  if(px<0||py<0||px>=rect.width||py>=rect.height)return null;
  pickPointer.set(px/rect.width*2-1,1-py/rect.height*2);
  pickRay.setFromCamera(pickPointer,camera);
  const objects=includePorts?[model,portsGroup]:[model];
  return pickRay.intersectObjects(objects,true).find(hit=>{
   if(!hit.object.isMesh)return false;
   for(let object=hit.object;object;object=object.parent)if(!object.visible)return false;
   return true;
  })||null;
 }
 let hit=hitAt(x,y,true);
 // Busca cerca del cursor únicamente si el clic no tocó una superficie.
 for(const radius of [1.5,3]){
  if(hit)break;
  const nearby=[];
  for(let i=0;i<8;i++){
   const angle=i*Math.PI/4;
   const candidate=hitAt(x+Math.cos(angle)*radius,y+Math.sin(angle)*radius,false);
   if(candidate)nearby.push(candidate);
  }
  nearby.sort((a,b)=>a.distance-b.distance);
  hit=nearby[0];
 }
 if(!hit)return;
 if(hit.object.userData.weldComponentId){const id=hit.object.userData.weldComponentId;selectNode(id);$('weld-list').value=id;status('Cordón seleccionado. Puedes eliminarlo desde Soldaduras y división en segmentos.');return;}
 if(hit.object.userData.portId){continueFrom(hit.object.userData.portId);return;}
 let part=hit.object;
 while(part&&!part.userData.id&&!part.userData.equipmentId&&!part.userData.repairId)part=part.parent;
 if(part?.userData.repairId){$('repair-list').value=part.userData.repairId;$('repair-list').onchange();status('Reparación seleccionada. Sus cambios se actualizan automáticamente.');}
 else if(part?.userData.id)selectNode(part.userData.id);
 else if(part?.userData.equipmentId)selectEquipment(part.userData.equipmentId);
});
async function capture(){
 const old={position:camera.position.clone(),target:controls.target.clone(),up:camera.up.clone(),left:camera.left,right:camera.right,top:camera.top,bottom:camera.bottom,zoom:camera.zoom,near:camera.near,far:camera.far,bg:scene.background},size=renderer.getSize(new THREE.Vector2()),pixel=renderer.getPixelRatio(),box=scene.getObjectByName('selection-box');
 capturing=true;controls.enabled=false;
 try{
  portsGroup.visible=false;grid.visible=false;axes.visible=false;if(box)box.visible=false;scene.background=new THREE.Color(0xffffff);renderer.setPixelRatio(1);renderer.setSize(1600,900,false);fit('iso',1600/900);arrangeLabels();arrangeAnnotations(annotationsGroup,design,result,camera,renderer,true);renderer.render(scene,camera);return renderer.domElement.toDataURL('image/png');
 }finally{
  scene.background=old.bg;portsGroup.visible=true;grid.visible=true;axes.visible=true;if(box)box.visible=true;renderer.setPixelRatio(pixel);renderer.setSize(size.x,size.y,false);camera.position.copy(old.position);controls.target.copy(old.target);camera.up.copy(old.up);for(const key of ['left','right','top','bottom','zoom','near','far'])camera[key]=old[key];camera.updateProjectionMatrix();controls.enabled=true;controls.update();capturing=false;arrangeLabels();arrangeAnnotations(annotationsGroup,design,result,camera,renderer);
 }
}
function refreshDetailUI(){const weldId=$('weld-list').value,welds=design.components.filter(c=>c.weldTag);$('weld-list').replaceChildren(...welds.map(c=>new Option(c.weldTag+' · '+(design.components.find(a=>c.parentPort===a.id+':out')?.tag||'entrada')+' / '+c.tag,c.id)));if(welds.some(c=>c.id===weldId))$('weld-list').value=weldId;else if(welds.some(c=>c.id===selected))$('weld-list').value=selected;$('weld-remove').disabled=$('weld-hide').disabled=!welds.length;
 const old=$('repair-host').value;$('repair-host').replaceChildren(...result.nodes.filter(n=>n.kind==='pipe').map(n=>new Option(n.tag+' · '+item(catalog,n.nps).label,n.id)));if(result.nodes.some(n=>n.id===old&&n.kind==='pipe'))$('repair-host').value=old;
 if(!(design.repairs||[]).some(r=>r.id===selectedRepairId))selectedRepairId=null;if(!(design.annotations||[]).some(a=>a.id===selectedAnnotationId))selectedAnnotationId=null;
 $('repair-list').replaceChildren(...(design.repairs||[]).map(r=>new Option(r.tag+' · '+REPAIRS[r.type],r.id)));$('repair-list').value=selectedRepairId||'';
 $('annotation-list').replaceChildren(...(design.annotations||[]).map(a=>new Option(a.number+' · '+a.text.slice(0,55),a.id)));$('annotation-list').value=selectedAnnotationId||'';
 $('repair-delete').disabled=!selectedRepairId;$('annotation-delete').disabled=!selectedAnnotationId;$('repair-add').disabled=!$('repair-host').value;$('repair-coverage').disabled=$('repair-type').value==='type_b';
}
function repairForm(id){return {id,hostId:$('repair-host').value,type:$('repair-type').value,tag:$('repair-tag').value.trim()||'REP'+String((design.repairs||[]).length+1).padStart(2,'0'),comment:$('repair-comment').value,startMM:Number($('repair-start').value),lengthMM:Number($('repair-length').value),thicknessMM:Number($('repair-thickness').value),coverageDeg:Number($('repair-coverage').value),rollDeg:Number($('repair-roll').value)};}
function annotationFields(){return {number:$('annotation-number').value,text:$('annotation-text').value,color:$('annotation-color').value,style:$('annotation-style').value,offsetX:Number($('annotation-x').value),offsetY:Number($('annotation-y').value)};}
function placeAnnotation(ray){
 const hits=ray.intersectObjects(model.children,true);if(!hits.length){status('Elige un punto sobre el piping o un equipo.',true);return;}const hit=hits[0];let object=hit.object;while(object&&!object.userData.id&&!object.userData.equipmentId&&!object.userData.componentId)object=object.parent;if(!object)return;
 const equipmentId=object.userData.equipmentId,hostId=equipmentId||object.userData.id||object.userData.componentId,hostType=equipmentId?'equipment':'component',coordinates=equipmentId?equipmentModel.children.find(g=>g.userData.equipmentId===equipmentId).worldToLocal(hit.point.clone()).toArray():componentCoordinates(result.nodes.find(n=>n.id===hostId),hit.point.toArray());
 const id='a'+uid().slice(0,24),annotation={id,hostType,hostId,coordinates,...annotationFields()};selectedAnnotationId=id;
 if(mutate(d=>{d.annotations||=[];d.annotations.push(annotation);})){marking=false;renderer.domElement.style.cursor='';$('annotation-place').textContent='Elegir punto para nueva marca';status('Marca '+annotation.number+' agregada. Se guardará con el proyecto.');}
}
function updateRepair(){if(!selectedRepairId)return true;const id=selectedRepairId;return mutate(d=>{const index=(d.repairs||[]).findIndex(r=>r.id===id);if(index>=0)d.repairs[index]=repairForm(id);});}
function updateAnnotation(){if(!selectedAnnotationId)return true;return mutate(d=>{const a=(d.annotations||[]).find(a=>a.id===selectedAnnotationId);if(a)Object.assign(a,annotationFields());});}
$('repair-new').onclick=()=>{selectedRepairId=null;$('repair-tag').value='REP'+String((design.repairs||[]).length+1).padStart(2,'0');$('repair-comment').value='';const host=result.nodes.find(n=>n.id===$('repair-host').value);$('repair-start').value=0;if(host)$('repair-length').value=Math.min(200,host.length);refreshDetailUI();};
$('repair-add').onclick=()=>{selected=null;selectedEquipmentId=null;const id='r'+uid().slice(0,24);selectedRepairId=id;mutate(d=>{d.repairs||=[];d.repairs.push(repairForm(id));});};
$('repair-list').onchange=()=>{selected=null;selectedEquipmentId=null;selectedRepairId=$('repair-list').value;const r=(design.repairs||[]).find(r=>r.id===selectedRepairId);if(!r)return;for(const [id,key] of [['repair-host','hostId'],['repair-type','type'],['repair-tag','tag'],['repair-start','startMM'],['repair-length','lengthMM'],['repair-thickness','thicknessMM'],['repair-roll','rollDeg'],['repair-coverage','coverageDeg'],['repair-comment','comment']])$(id).value=r[key];refresh();highlight();};
$('repair-delete').onclick=()=>{mutate(d=>{d.repairs=d.repairs.filter(r=>r.id!==selectedRepairId);});};
$('repair-host').onchange=()=>{const n=result.nodes.find(n=>n.id===$('repair-host').value);if(n&&!selectedRepairId){$('repair-start').value=0;$('repair-length').value=Math.min(200,n.length);}updateRepair();};
for(const id of ['repair-type','repair-tag','repair-start','repair-length','repair-thickness','repair-roll','repair-coverage','repair-comment']){$(id).addEventListener('input',()=>{clearTimeout(detailTimer);detailTimer=setTimeout(updateRepair,160);});$(id).addEventListener('change',()=>{clearTimeout(detailTimer);updateRepair();refreshDetailUI();});}
$('annotation-place').onclick=()=>{setWeldMode(false);if(selectedAnnotationId){const n=Number($('annotation-number').value);if(Number.isFinite(n))$('annotation-number').value=n+1;}selectedAnnotationId=null;marking=!marking;renderer.domElement.style.cursor=marking?'crosshair':'';$('annotation-place').textContent=marking?'Cancelar elección de punto':'Elegir punto para nueva marca';refreshDetailUI();status(marking?'Haz clic sobre el punto del dibujo que quieres señalar.':'Marcado cancelado.');};
$('annotation-list').onchange=()=>{selectedAnnotationId=$('annotation-list').value;const a=(design.annotations||[]).find(a=>a.id===selectedAnnotationId);if(!a)return;for(const [id,key] of [['annotation-number','number'],['annotation-text','text'],['annotation-style','style'],['annotation-color','color'],['annotation-x','offsetX'],['annotation-y','offsetY']])$(id).value=a[key];refreshDetailUI();};
$('annotation-delete').onclick=()=>mutate(d=>{d.annotations=d.annotations.filter(a=>a.id!==selectedAnnotationId);});
for(const id of ['annotation-number','annotation-text','annotation-style','annotation-color','annotation-x','annotation-y']){$(id).addEventListener('input',()=>{clearTimeout(detailTimer);detailTimer=setTimeout(updateAnnotation,160);});$(id).addEventListener('change',()=>{clearTimeout(detailTimer);updateAnnotation();});}
function guard(fn){return async()=>{try{await fn();}catch(e){status(e.message,true);}};}
let liveTimer=null,liveUndoTimer=null,liveSelection=null;
function setWeldMode(on){weldMode=on;$('weld-mode').classList.toggle('active',on);$('weld-mode').textContent=on?'Cancelar elección de soldadura':'Elegir punto de soldadura en el dibujo';renderer.domElement.style.cursor=on?'crosshair':'';}
function deleteWeld(join){try{if(!updateSelected())return;const output=removeWeld(design,$('weld-list').value,catalog,join);setWeldMode(false);selected=null;setDesign(output.design);selectNode(output.id);status('Cordón '+output.weldTag+' eliminado. '+(join?'Los tramos quedaron unidos.':'Se conservan los segmentos y sus formas.'));}catch(error){status(error.message,true);}}
$('weld-remove').onclick=()=>deleteWeld(true);$('weld-hide').onclick=()=>deleteWeld(false);
$('weld-mode').onclick=()=>{if(!updateSelected())return;marking=false;$('annotation-place').textContent='Elegir punto para nueva marca';setWeldMode(!weldMode);status(weldMode?'Haz clic en el punto del tubo donde irá el cordón de soldadura.':'Selección de soldadura cancelada.');};
function updateSelected(){
 clearTimeout(liveTimer);if(!selected)return true;const current=design.components.find(c=>c.id===selected);if(!current)return true;
 const edited=form();if(JSON.stringify(current)===JSON.stringify(edited))return true;
 try{const next=structuredClone(design);next.components[next.components.findIndex(c=>c.id===selected)]=edited;if(current.kind==='valve'&&edited.kind==='valve'&&(current.valveConnection||'flanged')!==(edited.valveConnection||'flanged'))adaptValveEdit(next,selected,catalog);next.components=sortComponents(next,catalog).components;setDesign(next,liveSelection!==selected);liveSelection=selected;clearTimeout(liveUndoTimer);liveUndoTimer=setTimeout(()=>{liveSelection=null;},800);status('Cambios actualizados en '+edited.tag+'.');return true;}catch(error){status(error.message,true);return false;}
}
for(const id of ['pad-length','pad-thickness','pad-coverage','pipe-x','pipe-y','pipe-z','pipe-yaw','pipe-pitch','pipe-curve','pipe-curve-roll','inlet-end','valve-connection','tee-entry','tee-run-nps','branch-yaw','branch-pitch','olet-angle','run-pipe','tap-offset','outlet-end','branch-end','tag','nps','rating','out-nps','outlet-rating','length','radius','branch-length','roll','bend','reduction','valve-type']){
 $(id).addEventListener('input',()=>{clearTimeout(liveTimer);if(selected)liveTimer=setTimeout(updateSelected,160);});
 $(id).addEventListener('change',()=>{if(selected)updateSelected();});
}
$('add').onclick=guard(()=>{if(selected)return;if(!activePort&&!['sockolet','thredolet','latrolet','elbolet','poncho'].includes(kindValue()))throw Error('No hay un extremo libre.');const c=form();c.id='c'+uid().slice(0,24);if(!isOlet(c))c.parentPort=activePort;if(!mutate(d=>d.components.push(c)))return;selected=null;continuationId=c.id;if(isOlet(c))$('kind').value='pipe';activePort=result.freePorts.find(p=>p.id===c.id+':out')?.id||result.freePorts.at(-1)?.id||'';defaults();renderModel();refresh();status(c.kind==='gauge'?'Manómetro conectado al niple NPT macho.':c.outletEnd==='vent45'?'Niple de venteo agregado. La boca a 45° es terminal.':c.kind==='cap'?'Extremo cerrado. Elige otro extremo libre para continuar.':c.kind==='tee'?'Tee agregada. Elige lado A, lado B o derivación entre las bocas libres.':'Elemento conectado. Puedes continuar desde su salida o elegir otro extremo libre.');});
$('apply').onclick=()=>{if(!selected)return;const c=form();if(mutate(d=>{d.components[d.components.findIndex(n=>n.id===selected)]=c;}))selectNode(selected);};
$('delete').onclick=()=>{
 const component=design.components.find(c=>c.id===selected);
 if(!component)return;
 const ids=descendants(design,component.id);
 if(ids.size>1&&!confirm('¿Eliminar '+component.tag+' y sus '+(ids.size-1)+' componentes conectados aguas abajo? Puedes deshacerlo.'))return;
 clearTimeout(liveTimer);
 liveSelection=null;
 if(!mutate(d=>{d.components=d.components.filter(c=>!ids.has(c.id));removeDetails(d,ids);}))return;
 continuationId=null;
 if(result.freePorts.some(p=>p.id===component.parentPort))activePort=component.parentPort;
 defaults();renderModel();refresh();
 status('Se eliminó '+component.tag+(ids.size>1?' y su continuación.':'.')+' Puedes recuperarlo con Deshacer.');
};
$('clear').onclick=()=>{selected=null;defaults();refresh();highlight();};$('reduction').onchange=()=>{if(kindValue()==='reducer')$('kind').value='reducer-'+$('reduction').value;};$('valve-connection').onchange=conditional;$('outlet-end').onchange=conditional;$('tee-entry').onchange=()=>{conditional();height();};$('olet-angle').onchange=()=>{conditional();height();};$('run-pipe').onchange=()=>{const run=result.nodes.find(n=>n.id===$('run-pipe').value);if(run){$('tap-offset').max=run.length;if(!selected)$('tap-offset').value=run.length/2;}conditional();refreshContinuation();};$('kind').onchange=()=>{if(['reducer-concentric','reducer-eccentric'].includes($('kind').value))$('reduction').value=$('kind').value==='reducer-eccentric'?'eccentric':'concentric';if(['psv','rv'].includes(kindValue())){$('valve-type').value=kindValue();$('kind').value='valve';}if(selected){conditional();updateSelected();}else defaults();};$('nps').onchange=()=>{if(selected){conditional();updateSelected();}else defaults();};$('rating').onchange=conditional;$('valve-type').onchange=conditional;$('port').onchange=()=>continueFrom($('port').value);$('component-list').onchange=()=>selectNode($('component-list').value);
$('equipment').onchange=()=>selectEquipment($('equipment').value);$('equipment-edit').onclick=()=>{if(equipmentTimer){clearTimeout(equipmentTimer);equipmentTimer=null;$('equipment-apply').click();}const id=$('equipment').value;if(!id)return;notify('edit_equipment',{equipmentId:id,eventId:uid()});};
$('equipment-apply').onclick=()=>mutate(d=>{const e=d.equipments.find(e=>e.id===$('equipment').value);e.position=['equipment-x','equipment-y','equipment-z'].map(id=>Number($(id).value));e.rotationDeg=Number($('equipment-rotation').value);});
let equipmentTimer=null;for(const id of ['equipment-x','equipment-y','equipment-z','equipment-rotation'])$(id).addEventListener('input',()=>{clearTimeout(equipmentTimer);equipmentTimer=setTimeout(()=>{equipmentTimer=null;if(['equipment-x','equipment-y','equipment-z','equipment-rotation'].every(k=>$(k).value.trim()!==''))$('equipment-apply').click();},180);});
$('equipment-remove').onclick=()=>mutate(d=>{const id=$('equipment').value;if(d.components.some(c=>c.parentPort.startsWith('eq-'+id+'/')))throw Error('Desacopla o elimina primero las líneas conectadas al equipo.');d.equipments=d.equipments.filter(e=>e.id!==id);removeDetails(d,new Set(),new Set([id]));});
$('attach').onclick=()=>{if(!selected||!activePort)return;const target=activePort,id=selected;if(mutate(d=>{const c=d.components.find(c=>c.id===id);c.parentPort=target;d.components=sortComponents(d,catalog).components;}))status('Línea acoplada al extremo seleccionado, incluyendo su continuación.');};
$('title').onchange=()=>mutate(d=>{d.title=$('title').value.trim()||'Línea de piping';});$('direction').onchange=()=>mutate(d=>{d.direction=$('direction').value;});
$('undo').onclick=()=>{clearTimeout(liveTimer);liveSelection=null;if(!undo.length)return;redo.push(structuredClone(design));const d=undo.pop();selected=null;setDesign(d,false);defaults();};$('redo').onclick=()=>{clearTimeout(liveTimer);liveSelection=null;if(!redo.length)return;undo.push(structuredClone(design));const d=redo.pop();selected=null;setDesign(d,false);defaults();};
$('line-color-apply').onclick=()=>setLineColor($('line-color').value);
$('line-color-reset').onclick=()=>setLineColor(null);
$('panel-undo').onclick=()=>$('undo').click();
$('panel-redo').onclick=()=>$('redo').click();
function flushProject(){
 if(detailTimer){clearTimeout(detailTimer);detailTimer=null;if(updateRepair()===false||updateAnnotation()===false)throw Error('Corrige los datos de la reparación o marca antes de guardar.');}
 if(updateSelected()===false)throw Error('Corrige los valores del componente antes de guardar.');
 if(equipmentTimer){clearTimeout(equipmentTimer);equipmentTimer=null;if($('equipment-apply').onclick()===false)throw Error('Revisa la posición del equipo.');}
 validateDesign(design,catalog);
}
async function refreshProjects(){const projects=await listLocal();$('project-list').replaceChildren(...projects.map(p=>new Option(p.name+' · '+new Date(p.updatedAt).toLocaleString('es-CL'),p.name)));$('project-load-local').disabled=!projects.length;}
async function openProjectDialog(){try{$('project-name').value=design.title;await refreshProjects();$('project-save-cloud').disabled=!serverArgs.project_cloud_ready;$('project-location').textContent=serverArgs.project_cloud_ready?'Google Drive está conectado. Guarda allí para abrir el proyecto desde otro computador. La copia local pertenece a este navegador.':'Puedes guardar por nombre en este navegador. Para continuar desde otro computador, activa Google Drive en Proyectos entre computadores.';$('project-status').textContent='';$('project-dialog').showModal();}catch(error){status(error.message,true);}}
$('project-save').onclick=openProjectDialog;$('project-open').onclick=openProjectDialog;$('project-close').onclick=()=>$('project-dialog').close();
$('project-save-local').onclick=async()=>{try{flushProject();const name=$('project-name').value.trim();if(!name)throw Error('Escribe un nombre para el proyecto.');if(!mutate(d=>{d.title=name;}))return;$('project-status').textContent='Guardando copia completa…';await saveLocal(name,design);lastBackupAt=new Date().toLocaleString('es-CL');await refreshProjects();$('project-status').textContent='Guardado: '+name+'. Puedes abrirlo desde Mis proyectos en este navegador.';$('backup-info').textContent='Proyecto '+name+' guardado en este navegador el '+new Date().toLocaleString('es-CL')+'. Para otro computador usa Google Drive.';}catch(error){$('project-status').textContent=error.message;}};
$('project-load-local').onclick=async()=>{try{const projects=await listLocal(),project=projects.find(p=>p.name===$('project-list').value);if(!project)return;selected=null;setDesign(structuredClone(project.design),true,true);defaults();refresh();$('project-dialog').close();status('Proyecto abierto: '+project.name);}catch(error){$('project-status').textContent=error.message;}};
$('project-save-cloud').onclick=()=>{try{flushProject();const name=$('project-name').value.trim();if(!name)throw Error('Escribe un nombre para el proyecto.');if(!mutate(d=>{d.title=name;}))return;const eventId=uid();pendingCloud={eventId,snapshot:JSON.stringify(design)};notify('save_project',{eventId,projectName:name});$('project-status').textContent='Guardando y verificando en Google Drive…';}catch(error){$('project-status').textContent=error.message;}};
$('save').onclick=guard(()=>{if(detailTimer){clearTimeout(detailTimer);detailTimer=null;if(updateRepair()===false||updateAnnotation()===false)throw Error('Corrige los datos de la reparación o marca antes de guardar.');}
 if(updateSelected()===false)throw Error('Corrige los valores del componente antes de guardar el proyecto.');
 if(equipmentTimer){clearTimeout(equipmentTimer);equipmentTimer=null;if(['equipment-x','equipment-y','equipment-z','equipment-rotation'].some(id=>$(id).value.trim()===''))throw Error('Completa la posición del equipo antes de guardar.');if($('equipment-apply').onclick()===false)throw Error('Revisa la posición del equipo antes de guardar.');}
 validateDesign(design,catalog);const now=new Date(),stamp=now.getFullYear()+'-'+String(now.getMonth()+1).padStart(2,'0')+'-'+String(now.getDate()).padStart(2,'0')+'_'+String(now.getHours()).padStart(2,'0')+'-'+String(now.getMinutes()).padStart(2,'0')+'-'+String(now.getSeconds()).padStart(2,'0');
 lastBackupFile=filename()+'_'+stamp+'.json';exportFile(lastBackupFile,JSON.stringify(design,null,2),'application/json');lastBackupAt=now.toLocaleString('es-CL');backupInfo(false);status('Respaldo completo preparado: '+(design.equipments||[]).length+' equipos y '+design.components.length+' componentes. Revisa la descarga del archivo JSON.');
});$('load').onclick=()=>$('file').click();$('file').onchange=guard(async()=>{const f=$('file').files[0];if(!f)return;if(f.size>32e6)throw Error('El JSON supera 32 MB.');setDesign(JSON.parse(await f.text()),true,true);selected=null;defaults();refresh();status('Proyecto abierto: '+(design.equipments||[]).length+' equipos y '+design.components.length+' componentes. Puedes continuar editando.');backupInfo();$('file').value='';});
$('example').onclick=guard(async()=>{if((design.components.length||(design.equipments||[]).length)&&!confirm('¿Abrir el ejemplo? Podrás recuperar el diseño actual con Deshacer.'))return;selected=null;setDesign(await fetch('./ejemplo.json').then(r=>r.json()));activePort=result.freePorts.at(-1)?.id||'';defaults();refresh();fit('iso');status('Ejemplo cargado. Selecciona un elemento para editarlo o continúa desde un extremo.');});
$('new').onclick=()=>{if((design.components.length||(design.equipments||[]).length)&&!confirm('¿Comenzar una línea nueva? Descarga antes el JSON si deseas conservar la actual.'))return;selected=null;activePort='origin';setDesign(blankDesign('p'+uid()),true,true);defaults();refresh();};
for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>fit(b.dataset.view==='fit'?'current':b.dataset.view);
$('labels').onclick=()=>{labelsVisible=!labelsVisible;labelsGroup.visible=labelsVisible;$('labels').textContent=labelsVisible?'Ocultar TAG':'Mostrar TAG';};
$('png').onclick=guard(async()=>{const data=await capture();const a=document.createElement('a');a.href=data;a.download=filename()+'.png';a.click();});
$('pdf').onclick=guard(async()=>{if(!design.components.length&&!(design.equipments||[]).length)throw Error('Agrega componentes o equipos antes de exportar.');status('Preparando isométrico y materiales…');notify('export_pdf',{image:await capture()});status('Captura lista. Descarga el PDF debajo del editor.');});
window.addEventListener('message',e=>{if(e.data.type!=='streamlit:render')return;serverArgs=e.data.args||{};const initialize=!loaded||loadToken!==serverArgs.load_token;loadToken=serverArgs.load_token;loaded=true;
 try{if(serverArgs.project_ack&&serverArgs.project_ack.eventId!==lastProjectAck){const ack=serverArgs.project_ack;lastProjectAck=ack.eventId;if(ack.ok&&pendingCloud?.eventId===ack.eventId){const dirty=pendingCloud&&JSON.stringify(design)!==pendingCloud.snapshot;design.cloudProject=ack.project;if(!dirty)lastBackupAt=new Date().toLocaleString('es-CL');try{localStorage.setItem(STORAGE,JSON.stringify(design));}catch{}$('project-status').textContent='Guardado y verificado en Google Drive: '+ack.project.name+(dirty?'. Hay cambios posteriores pendientes.':'.');$('backup-info').textContent=$('project-status').textContent;}else if(!ack.ok)$('project-status').textContent='No se pudo confirmar el guardado: '+ack.error;pendingCloud=null;}if(initialize){let initial=serverArgs.initial_data||blankDesign();if(!serverArgs.imported){try{const saved=JSON.parse(localStorage.getItem(STORAGE));if(saved?.version===1&&(!initial.components.length||saved.updatedAt>initial.updatedAt))initial=saved;}catch{}}
 validateDesign(initial,catalog);for(const e of initial.equipments||[])validateAsset(e.asset);design=structuredClone(initial);result=compute(design,catalog);activePort=result.freePorts.at(-1)?.id||'';selected=null;renderModel();fit('iso');refresh();$('nps').value=2;defaults();notify();status('Diseño listo. El respaldo automático se conserva en este navegador.');}
 if(serverArgs.equipment_import&&serverArgs.equipment_import_token!==design.equipmentImportToken){const token=serverArgs.equipment_import_token,e=serverArgs.equipment_import;const ok=mutate(d=>{d.equipments ||= [];const i=d.equipments.findIndex(old=>old.id===e.id);if(i>=0)d.equipments[i]={...e,position:d.equipments[i].position,rotationDeg:d.equipments[i].rotationDeg};else d.equipments.push(e);d.equipmentImportToken=token;});if(ok){notify('equipment_applied',{equipmentApplied:token});status('Equipo incorporado. Elige una boquilla para continuar el piping.');}else notify('equipment_error',{equipmentApplied:token});}
 else if(serverArgs.equipment_import_token&&serverArgs.equipment_import_token===design.equipmentImportToken)notify('equipment_applied',{equipmentApplied:design.equipmentImportToken});
 }catch(err){status(err.message,true);}
});
function animate(){requestAnimationFrame(animate);controls.update();arrangeLabels();arrangeAnnotations(annotationsGroup,design,result,camera,renderer,capturing);renderer.render(scene,camera);}animate();renderModel();fit('iso');refresh();$('nps').value=2;defaults();send('streamlit:componentReady',{apiVersion:1});height();
// Inspección de geometría sin datos privados para pruebas y soporte.
window.pipingEditor={getDesign:()=>structuredClone(design),getResult:()=>result,load:d=>setDesign(d),capture,scene,camera,model,renderer};
