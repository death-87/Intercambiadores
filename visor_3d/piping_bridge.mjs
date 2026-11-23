// Exportación pasiva del equipo: geometrías, materiales y transformaciones; sin texturas.
export function equipmentAsset(THREE,source,excluded=null){
 const geometries=new Map(),materials=new Map();
 function copy(node){
  if(node===excluded||!node.visible||node.isSprite||node.isLine||node.isLight||node.isCamera)return null;
  const saved=node.userData;node.userData={};let target;
  try{target=node.clone(false);}finally{node.userData=saved;}
  target.userData={};
  if(node.geometry){if(!geometries.has(node.geometry))geometries.set(node.geometry,new THREE.BufferGeometry().copy(node.geometry));target.geometry=geometries.get(node.geometry);}
  if(node.material){const material=m=>{if(!materials.has(m)){const c=new THREE.MeshStandardMaterial({color:m.userData?.selectionColor||m.color||0x9ba8b1,metalness:m.metalness??.3,roughness:m.roughness??.5,side:m.side,transparent:m.transparent,opacity:m.opacity});materials.set(m,c);}return materials.get(m);};target.material=Array.isArray(node.material)?node.material.map(material):material(node.material);}
  for(const child of node.children){const c=copy(child);if(c)target.add(c);}return target;
 }
 const root=new THREE.Group();root.rotation.x=Math.PI/2;root.scale.setScalar(1000);root.add(copy(source));
 try{root.updateMatrixWorld(true);const data=root.toJSON();for(const g of data.geometries||[])for(const attr of [...Object.values(g.data?.attributes||{}),g.data?.index].filter(Boolean)){const Type=globalThis[attr.type],array=new Type(attr.array),bytes=new Uint8Array(array.buffer);let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));attr.array64=btoa(binary);delete attr.array;}
 const asset={format:'three-buffer-v1',data};if(JSON.stringify(asset).length>16000000)throw Error('El equipo supera el tamaño admitido. Reduce la cantidad de elementos.');return asset;
 }finally{for(const g of geometries.values())g.dispose();for(const m of materials.values())m.dispose();}
}
