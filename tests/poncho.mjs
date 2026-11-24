import assert from 'node:assert/strict';
import fs from 'node:fs';
import {compute,materialRows} from '../visor_piping/model.mjs';
import {ponchoMesh} from '../visor_piping/poncho.mjs';
import {splitPipe,removeWeld} from '../visor_piping/split_pipe.mjs';
const catalog=JSON.parse(fs.readFileSync(new URL('../visor_piping/catalogo.json',import.meta.url))),example=JSON.parse(fs.readFileSync(new URL('../visor_piping/ejemplo.json',import.meta.url)));
const root={...example.components[0],id:'main',tag:'MAIN',parentPort:'origin',nps:6,lengthMM:3000,pipeYawDeg:15,pipePitchDeg:20,pipeCurveDeg:10,pipeCurveRollDeg:90};
const pad={...root,id:'pad',tag:'PR01',kind:'poncho',parentPort:'main:tap',tapOffsetMM:1500,outNps:2,lengthMM:150,rollDeg:45,padLengthMM:300,padThicknessMM:8,padCoverageDeg:150};
const child={...root,id:'branch',tag:'BRANCH',parentPort:'pad:out',nps:2,lengthMM:500,pipeCurveDeg:0,pipePitchDeg:0,pipeYawDeg:0};
const design={...example,components:[root,pad,child]},result=compute(design,catalog),node=result.nodes[1];
assert.equal(result.nodes[2].nps,2);assert.equal(result.ports.get('pad:out').endType,'plain');assert.equal(node.pad.thickness,8);assert.ok(result.freePorts.some(p=>p.id==='main:out'));const mesh=ponchoMesh(node);assert.ok(mesh.positions.every(Number.isFinite));assert.ok(mesh.indices.every(i=>i>=0&&i<mesh.positions.length/3));assert.ok(mesh.outer.length>30);
for(const changes of [{padThicknessMM:-1},{padCoverageDeg:1},{padLengthMM:20},{tapOffsetMM:40},{outNps:8},{outNps:6},{lengthMM:10,padThicknessMM:20}]){const invalid=structuredClone(design);Object.assign(invalid.components[1],changes);assert.throws(()=>compute(invalid,catalog));}
const before=result.nodes[2].end,split=splitPipe(design,'main',700,catalog,'second'),after=compute(split.design,catalog).nodes.find(n=>n.id==='branch').end;assert.ok(Math.hypot(...after.map((x,i)=>x-before[i]))<1e-6);const joined=removeWeld(split.design,'second',catalog);assert.equal(joined.design.components.find(c=>c.id==='pad').tapOffsetMM,1500);
console.log(JSON.stringify({design,materials:materialRows(result,catalog)}));
