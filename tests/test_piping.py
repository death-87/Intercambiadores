"""Conexiones, catálogo compartido y exportaciones del editor de piping."""
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from piping_core import CATALOGO, MEDIDAS, validar_piping, materiales_piping

ROOT=Path(__file__).resolve().parents[1]


class PipingTests(unittest.TestCase):
    def setUp(self):
        self.design=json.loads((ROOT/'visor_piping'/'ejemplo.json').read_text())

    def test_catalogo_compartido(self):
        self.assertEqual(len(CATALOGO['items']),17)
        self.assertEqual(MEDIDAS[2]['odMM'],60.3)
        self.assertEqual(MEDIDAS[2.5]['odMM'],73)
        self.assertEqual(MEDIDAS[2]['flanges']['300#']['diameterMM'],165.1)
        self.assertEqual(MEDIDAS[2]['flanges']['300#']['boltCount'],8)
        self.assertEqual(set(MEDIDAS[2]['flanges']),{'150#','300#','600#'})

    def test_materiales_incluyen_contrapartes(self):
        rows=materiales_piping(self.design)
        self.assertEqual(sum(r['quantity'] for r in rows if r['description']=='Brida WN'),5)
        pipes=next(r for r in rows if r['description']=='Tramo recto' and r['nps']=='2"')
        self.assertEqual((pipes['quantity'],pipes['lengthMM']),(2,1500))
        valves=next(r for r in rows if r['description'].startswith('Válvula'))
        self.assertEqual((valves['rating'],valves['quantity']),('300#',1))

    def test_rechaza_conexiones_rotas_o_duplicadas(self):
        for parent in ['inexistente:out','p1:out','bc1:out']:
            design=copy.deepcopy(self.design)
            node=copy.deepcopy(design['components'][0]);node.update(id='otro',parentPort=parent)
            design['components'].append(node)
            with self.subTest(parent=parent),self.assertRaises(ValueError):validar_piping(design)
        design=copy.deepcopy(self.design);design['components'][0]['lengthMM']=float('nan')
        with self.assertRaises(ValueError):validar_piping(design)
        design=copy.deepcopy(self.design);design['components'][4]['branchNps']=24
        with self.assertRaises(ValueError):validar_piping(design)

    @unittest.skipUnless(shutil.which('node'),'Node no está instalado')
    def test_materiales_coinciden_con_motor_3d(self):
        code='''import fs from 'node:fs';import {compute,materialRows} from MODEL;const d=JSON.parse(fs.readFileSync(DESIGN,'utf8')),c=JSON.parse(fs.readFileSync(CATALOG,'utf8'));console.log(JSON.stringify(materialRows(compute(d,c),c)));'''
        code=code.replace('MODEL',json.dumps((ROOT/'visor_piping'/'model.mjs').as_uri())).replace('DESIGN',json.dumps(str(ROOT/'visor_piping'/'ejemplo.json'))).replace('CATALOG',json.dumps(str(ROOT/'visor_piping'/'catalogo.json')))
        actual=json.loads(subprocess.check_output(['node','--input-type=module','-e',code],text=True))
        self.assertEqual(actual,materiales_piping(self.design))

    @unittest.skipUnless(shutil.which('node'),'Node no está instalado')
    def test_equipo_valvulas_y_acoplamiento(self):
        result=json.loads(subprocess.check_output(['node',str(ROOT/'tests'/'piping_equipment.mjs')],text=True))
        design=result['design']
        self.assertEqual(validar_piping(design),design)
        self.assertEqual(materiales_piping(design),result['materials'])
        self.assertEqual(materiales_piping(result['endDesign']),result['endMaterials'])
        self.assertEqual(materiales_piping(result['socketDesign']),result['socketMaterials'])
        self.assertEqual(materiales_piping(result['oletDesign']),result['oletMaterials'])
        self.assertEqual(materiales_piping(result['latroletDesign']),result['latroletMaterials'])
        validar_piping(result['orientedDesign'])
        self.assertEqual(materiales_piping(result['teeDesign']),result['teeMaterials'])
        self.assertEqual(materiales_piping(result['threadedDesign']),result['threadedMaterials'])
        self.assertEqual(materiales_piping(result['convertedDesign']),result['convertedMaterials'])
        bad_thread=copy.deepcopy(result['threadedDesign']);bad_thread['components'][3]['valveConnection']='flanged'
        with self.assertRaises(ValueError):validar_piping(bad_thread)
        self.assertEqual(materiales_piping(result['teeBranchDesign']),result['teeBranchMaterials'])
        invalid=copy.deepcopy(result['orientedDesign']);invalid['components'][3]['branchPitchDeg']=91
        with self.assertRaises(ValueError):validar_piping(invalid)
        legacy=copy.deepcopy(result['oletDesign']);legacy['components'][3]['kind']='latrolet'
        self.assertEqual(materiales_piping(legacy),result['oletMaterials'])
        self.assertEqual(legacy['components'][3]['kind'],'elbolet')
        broken=copy.deepcopy(result['socketDesign']);broken['components'][1]['tapOffsetMM']=2100
        with self.assertRaises(ValueError):validar_piping(broken)
        self.assertEqual(sum(r['quantity'] for r in result['endMaterials'] if r['description']=='Brida WN'),5)
        plate_design=copy.deepcopy(design);plate_design['equipments'][0]['nameplate']={'matrix':[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]}
        validar_piping(plate_design)
        for plate in ({'matrix':[1]},'invalid',{'matrix':[float('nan')]*16}):
            plate_design['equipments'][0]['nameplate']=plate
            with self.assertRaises(ValueError):validar_piping(plate_design)
        broken=copy.deepcopy(design);broken['equipments'][0]['ports']=[]
        with self.assertRaises(ValueError):validar_piping(broken)
        broken=copy.deepcopy(design);broken['equipments'][0]['asset']['data']['images']=[{'url':'https://example.com/image'}]
        with self.assertRaises(ValueError):validar_piping(broken)

    def test_exportacion_pdf(self):
        from PIL import Image
        from pypdf import PdfReader
        from piping import pdf_piping
        buf=io.BytesIO();Image.new('RGB',(100,60),'white').save(buf,format='PNG')
        data=pdf_piping(self.design,buf.getvalue());reader=PdfReader(io.BytesIO(data))
        text='\n'.join(page.extract_text() for page in reader.pages)
        self.assertEqual(len(reader.pages),1)
        self.assertIn('Jndigital',text)
        self.assertIn('300#',text)
        self.assertIn('Codo 45',text)
        with self.assertRaises(ValueError):pdf_piping(self.design,b'invalid')


if __name__=='__main__':unittest.main()
