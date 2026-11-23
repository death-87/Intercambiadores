// Terminaciones NPT de niples y válvulas; diseños anteriores conservan sus uniones.
export function connection(c,origin){
 const threadedValve=c.kind==='valve'&&c.valveConnection==='threaded';
 const inletType=c.kind==='pipe'?(c.inletEnd==='threaded'||c.inletEnd!=='welded'&&origin.endType==='threaded'?'threaded':'plain'):threadedValve?'threaded':c.kind==='valve'?'flanged':'plain';
 if(origin.id!=='origin'){
  if(origin.endType==='threaded'&&inletType!=='threaded')throw Error('El extremo NPT requiere un niple o una válvula roscada.');
  if(origin.endType!=='threaded'&&inletType==='threaded')throw Error('Configura primero una salida roscada NPT en el componente anterior.');
  if(origin.endType==='threaded'&&origin.threadGender===(c.kind==='pipe'?'male':'female'))throw Error('La unión NPT necesita una rosca macho y una hembra. Intercala un niple o una unión compatible.');
 }
 return {inletType,threadedValve};
}
export function threadDetail(c,inletType,endType){
 if(c.kind==='valve'&&c.valveConnection==='threaded')return ' · roscada NPT';
 if(c.kind==='pipe'&&(inletType==='threaded'||endType==='threaded'))return ' · NPT '+(inletType==='threaded'&&endType==='threaded'?'ambos extremos':inletType==='threaded'?'entrada':'salida');
 return '';
}
