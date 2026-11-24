import assert from 'node:assert/strict';
import {reducerSection} from '../visor_piping/reducer_profile.mjs';
const n={start:[0,0,0],axis:[1,0,0],normal:[0,0,1],length:300,odMM:168.3,reduction:'concentric'};
for(const t of [0,.06,.12,.3,.5,.7,.88,.94,1]){let f=reducerSection(n,60.3,t);assert.equal(f.center[2],0);if(t<=.12)assert.equal(f.radius,168.3/2);if(t>=.88)assert.equal(f.radius,60.3/2);f=reducerSection({...n,reduction:'eccentric'},60.3,t);assert.ok(Math.abs(f.center[2]+f.radius-168.3/2)<1e-8);}
console.log('Reducciones BW: cuellos rectos, eje concéntrico y generatriz plana excéntrica OK');
