"""Valida el faldón sin iniciar Streamlit ni cargar servicios externos."""
import ast
import copy
import math
from pathlib import Path
import unittest


def funciones_del_modelo():
    source=ast.parse((Path(__file__).resolve().parents[1]/'Intercambiadores.py').read_text())
    nodes=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in {'validar_diseno','cuerpo_tecnico_boquilla'} or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'DIAMETROS','DIAMETROS_PULGADAS'} for t in n.targets)]
    namespace={'math':math}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'modelo_vertical','exec'),namespace)
    return namespace


class VerticalSkirtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.functions=funciones_del_modelo()

    def setUp(self):
        self.design={'model':'J','nameplate':'E-101','dimensions':{'shellLength':3,'shellDiameter':1,'verticalLowerEnd':'skirt','verticalSkirtLength':1.2},'nozzles':[]}

    def test_respaldo_con_faldon(self):
        self.assertEqual(self.functions['validar_diseno'](copy.deepcopy(self.design)),self.design)

    def test_limites_y_extremo_superior(self):
        for height in (.1,5.1,float('nan')):
            design=copy.deepcopy(self.design);design['dimensions']['verticalSkirtLength']=height
            with self.subTest(height=height),self.assertRaises(ValueError):self.functions['validar_diseno'](design)
        design=copy.deepcopy(self.design);design['dimensions']['verticalUpperEnd']='skirt'
        with self.assertRaises(ValueError):self.functions['validar_diseno'](design)

    def test_cuerpo_en_informe(self):
        self.assertEqual(self.functions['cuerpo_tecnico_boquilla']({'bodyPart':'bonnetLeft','pos':'axialMinus'},self.design),'FALDON DE APOYO')


if __name__=='__main__':unittest.main()
