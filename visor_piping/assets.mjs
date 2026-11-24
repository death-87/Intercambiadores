import * as THREE from 'three';
export function validateAsset(asset){
 const data=asset?.data;if(asset?.format!=='three-buffer-v1'||!data?.object||data.images?.length||data.textures?.length)throw Error('El equipo debe contener geometría pasiva, sin texturas externas.');
 if((data.geometries||[]).some(g=>g.type!=='BufferGeometry')||(data.materials||[]).some(m=>m.type!=='MeshStandardMaterial'))throw Error('Material o geometría de equipo no admitidos.');
 let count=0;function check(o,depth=0){if(++count>20000||depth>60||!['Group','Object3D','Mesh','InstancedMesh'].includes(o.type))throw Error('Objeto de equipo no admitido.');for(const c of o.children||[])check(c,depth+1);}check(data.object);return asset;
}
export function loadAsset(asset){
 validateAsset(asset);const data=structuredClone(asset.data),types={Float32Array,Uint32Array,Uint16Array,Uint8Array,Int32Array,Int16Array,Int8Array,Float64Array};
 for(const g of data.geometries||[])for(const a of [...Object.values(g.data?.attributes||{}),g.data?.index].filter(Boolean)){if(a.array64){const Type=types[a.type];if(!Type)throw Error('Atributo geométrico no admitido.');const binary=atob(a.array64),bytes=Uint8Array.from(binary,c=>c.charCodeAt(0));if(bytes.length>32000000)throw Error('Atributo demasiado grande.');a.array=Array.from(new Type(bytes.buffer));delete a.array64;}}
 return new THREE.ObjectLoader().parse(data);
}
