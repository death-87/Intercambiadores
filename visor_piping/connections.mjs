// Terminaciones NPT de niples y válvulas; diseños anteriores conservan sus uniones.
export function connection(c,origin){
 if(c.kind==='gauge'&&(origin.endType!=='threaded'||origin.threadGender!=='male'))throw Error('El manómetro requiere un niple con salida NPT macho.');
 const femaleThreaded=['couplingNPT','halfCouplingNPT'].includes(c.kind)||c.kind==='gauge'||c.kind==='valve'&&c.valveConnection==='threaded'||c.kind==='elbow'&&c.outletEnd==='threaded';
 const inletType=c.kind==='pipe'?(c.inletEnd==='threaded'||c.inletEnd!=='welded'&&origin.endType==='threaded'?'threaded':'plain'):femaleThreaded?'threaded':c.kind==='valve'?'flanged':'plain';
 if(origin.id!=='origin'){
  if(origin.endType==='threaded'&&inletType!=='threaded')throw Error('El extremo NPT requiere un accesorio con conexión roscada NPT compatible.');
  if(origin.endType!=='threaded'&&inletType==='threaded')throw Error('Configura primero una salida roscada NPT en el componente anterior.');
  if(origin.endType==='threaded'&&origin.threadGender===(c.kind==='pipe'?'male':'female'))throw Error('La unión NPT necesita una rosca macho y una hembra. Intercala un niple o una unión compatible.');
 }
 return {inletType,femaleThreaded};
}
export function threadDetail(c,inletType,endType){
 if(c.kind==='gauge')return ' · NPT hembra';
 if(c.outletEnd==='vent45')return ' · venteo a 45°'+(inletType==='threaded'?' · entrada NPT macho':'');
 if(c.kind==='elbow'&&endType==='threaded')return ' · roscado NPT hembra';
 if(c.kind==='valve'&&c.valveConnection==='threaded')return ' · roscada NPT';
 if(c.kind==='pipe'&&(inletType==='threaded'||endType==='threaded'))return ' · NPT '+(inletType==='threaded'&&endType==='threaded'?'ambos extremos':inletType==='threaded'?'entrada':'salida');
 return '';
}
