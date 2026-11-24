// Transición suave con cuellos rectos y pared hueca. No sustituye medidas del fabricante.
export function reducerSection(n,outsideDiameter,t){
 const r1=n.odMM/2,r2=outsideDiameter/2,u=Math.max(0,Math.min(1,(t-.12)/.76)),blend=u*u*(3-2*u),radius=r1+(r2-r1)*blend;
 const offset=n.reduction==='eccentric'?r1-radius:0;
 return {center:n.start.map((x,i)=>x+n.axis[i]*n.length*t+n.normal[i]*offset),radius};
}
