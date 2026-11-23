/** Servicio separado de proyectos de piping. No reemplaza guardar_diseno.gs. */
function configurarProyectosPiping() {
  const props=PropertiesService.getScriptProperties();
  if(!props.getProperty('PIPING_FOLDER_ID'))props.setProperty('PIPING_FOLDER_ID',DriveApp.createFolder('Jndigital - Proyectos Piping').getId());
  if(!props.getProperty('PIPING_TOKEN'))props.setProperty('PIPING_TOKEN',Utilities.getUuid()+Utilities.getUuid());
  console.log('Token para Streamlit (no compartir): '+props.getProperty('PIPING_TOKEN'));
}
function doPost(e) {
 const props=PropertiesService.getScriptProperties(),lock=LockService.getScriptLock();let locked=false;
 function output(value){return ContentService.createTextOutput(JSON.stringify(value)).setMimeType(ContentService.MimeType.JSON);}
 try{
  const request=JSON.parse(e.postData.contents),secret=props.getProperty('PIPING_TOKEN');
  if(!secret||typeof request.token!=='string'||request.token!==secret)throw Error('Acceso no autorizado.');
  if(request.action==='list'){
   const values=props.getProperties(),projects=Object.keys(values).filter(k=>k.startsWith('PROJECT_')).map(k=>JSON.parse(values[k])).map(p=>({id:p.id,name:p.name,revision:p.revision,updatedAt:p.updatedAt}));return output({ok:true,projects});
  }
  if(request.action==='load'){
   if(!/^[a-f0-9]{32}$/.test(request.id||''))throw Error('Proyecto inválido.');
   const metadata=JSON.parse(props.getProperty('PROJECT_'+request.id)||'null');if(!metadata)throw Error('No existe el proyecto.');
   const data=JSON.parse(DriveApp.getFileById(metadata.fileId).getBlob().getDataAsString('UTF-8'));return output({ok:true,design:data});
  }
  if(request.action!=='save')throw Error('Operación desconocida.');
  const name=String(request.name||'').trim();if(!name||name.length>120||!request.design||request.design.version!==1||!Array.isArray(request.design.components))throw Error('Nombre o proyecto inválido.');
  const digest=Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,name.toLowerCase(),Utilities.Charset.UTF_8),id=digest.map(b=>('0'+(b&255).toString(16)).slice(-2)).join('').slice(0,32);
  locked=lock.tryLock(30000);if(!locked)throw Error('Hay otro guardado en curso. Reintenta.');
  const old=JSON.parse(props.getProperty('PROJECT_'+id)||'null');
  if(old&&Number(request.revision)!==old.revision)throw Error('Este nombre ya tiene una versión más reciente. Abre el proyecto guardado o utiliza otro nombre.');
  const revision=(old?.revision||0)+1,updatedAt=new Date().toISOString(),data=request.design;data.title=name;data.cloudProject={id,name,revision,updatedAt};
  const raw=JSON.stringify(data);if(raw.length>30000000)throw Error('El proyecto supera el tamaño admitido.');
  const folder=DriveApp.getFolderById(props.getProperty('PIPING_FOLDER_ID')),file=folder.createFile(Utilities.newBlob(raw,'application/json',name+' - v'+revision+'.json'));
  // Verificar el archivo antes de anunciar el guardado. Las versiones previas se conservan.
  if(file.getBlob().getDataAsString('UTF-8')!==raw)throw Error('No se pudo verificar la copia guardada.');
  const metadata={id,name,revision,updatedAt,fileId:file.getId()};props.setProperty('PROJECT_'+id,JSON.stringify(metadata));
  return output({ok:true,project:{id,name,revision,updatedAt}});
 }catch(error){return output({ok:false,error:error.message});}finally{if(locked)lock.releaseLock();}
}
