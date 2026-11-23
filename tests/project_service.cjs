const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
const values={},files=new Map();let count=0;
const blob=text=>({getDataAsString:()=>text});
const folder={getId:()=> 'folder',createFile:b=>{const id='f'+(++count);files.set(id,b.text);return {getId:()=>id,getBlob:()=>blob(files.get(id))};}};
const sandbox={console:{log:()=>{}},PropertiesService:{getScriptProperties:()=>({getProperty:k=>values[k],setProperty:(k,v)=>{values[k]=v;},getProperties:()=>({...values})})},DriveApp:{createFolder:()=>folder,getFolderById:()=>folder,getFileById:id=>({getBlob:()=>blob(files.get(id))})},LockService:{getScriptLock:()=>({tryLock:()=>true,releaseLock:()=>{}})},Utilities:{getUuid:()=>crypto.randomUUID(),newBlob:text=>({text}),computeDigest:(_,s)=>crypto.createHash('sha256').update(s).digest(),DigestAlgorithm:{SHA_256:'sha'},Charset:{UTF_8:'utf8'}},ContentService:{MimeType:{JSON:'json'},createTextOutput:text=>({text,setMimeType(){return this;}})}};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync(require('node:path').join(__dirname,'../apps_script/proyectos_piping.gs'),'utf8'),sandbox);sandbox.configurarProyectosPiping();
function request(data){return JSON.parse(sandbox.doPost({postData:{contents:JSON.stringify({token:values.PIPING_TOKEN,...data})}}).text);}
assert.equal(request({action:'list',token:'wrong'}).ok,false);
const first=request({action:'save',name:'Equipo piping',design:{version:1,title:'old',components:[]}});assert.equal(first.ok,true);assert.equal(first.project.revision,1);
assert.equal(request({action:'save',name:'Equipo piping',design:{version:1,components:[]}}).ok,false);
const second=request({action:'save',name:'Equipo piping',revision:1,design:{version:1,components:[{id:'p'}]}});assert.equal(second.project.revision,2);assert.equal(files.size,2);
const loaded=request({action:'load',id:second.project.id});assert.equal(loaded.design.components[0].id,'p');assert.equal(loaded.design.cloudProject.revision,2);assert.equal(request({action:'list'}).projects.length,1);
assert.equal(request({action:'save',name:'Equipo piping',revision:1,design:{version:1,components:[]}}).ok,false);
console.log('Servicio de proyectos: autenticación, verificación, versiones anteriores, lectura y conflicto entre computadores OK');
