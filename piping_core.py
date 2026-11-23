"""Validación y materiales de diseños de piping. Longitudes en milímetros."""
from collections import OrderedDict
from pathlib import Path
import json
import math
import re

CATALOGO = json.loads((Path(__file__).parent / 'visor_piping' / 'catalogo.json').read_text())
MEDIDAS = {row['nps']: row for row in CATALOGO['items']}
TIPOS = {'pipe':'Tramo recto', 'elbow':'Codo', 'tee':'Tee', 'reducer':'Reductor', 'valve':'Válvula', 'flange':'Brida WN', 'cap':'Brida ciega'}
CLASES = {'150#','300#','600#'}


def validar_piping(diseno):
    if not isinstance(diseno, dict) or type(diseno.get('version')) is not int or diseno['version'] != 1:
        raise ValueError('El archivo no es un diseño de piping versión 1.')
    for campo, maximo in (('id',80),('title',120)):
        if not isinstance(diseno.get(campo),str) or len(diseno[campo]) > maximo:
            raise ValueError('Identificación del diseño inválida.')
    if diseno.get('direction') not in {'+X','-X','+Y','-Y','+Z','-Z'}:
        raise ValueError('Dirección inicial inválida.')
    componentes = diseno.get('components')
    if not isinstance(componentes,list) or len(componentes)>200:
        raise ValueError('El diseño admite hasta 200 componentes.')
    ids, usados, puertos = set(), set(), {'origin':(None,'plain',None)}
    for c in componentes:
        if not isinstance(c,dict) or not isinstance(c.get('id'),str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',c['id']) or c['id'] in ids or c.get('kind') not in TIPOS:
            raise ValueError('Componente inválido o repetido.')
        puerto = c.get('parentPort')
        if not isinstance(puerto,str) or puerto not in puertos or puerto in usados:
            raise ValueError('Existe una conexión ocupada o inexistente.')
        for k in ('nps','outNps','branchNps'):
            if type(c.get(k)) not in (int,float) or c[k] not in MEDIDAS:
                raise ValueError('Medida nominal fuera del catálogo.')
        if c.get('rating') not in CLASES or not isinstance(c.get('tag'),str) or len(c['tag'])>40:
            raise ValueError('TAG o clase inválidos.')
        for k, minimo, maximo in (('lengthMM',10,100000),('radiusMM',10,100000),('branchLengthMM',10,100000),('rollDeg',-3600,3600)):
            value=c.get(k)
            if type(value) not in (int,float) or not math.isfinite(value) or not minimo<=value<=maximo:
                raise ValueError('Dimensión inválida: '+k)
        if type(c.get('bendAngle')) not in (int,float) or c['bendAngle'] not in (45,90) or c.get('reduction') not in ('concentric','eccentric') or c.get('valveType') not in ('gate','ball'):
            raise ValueError('Configuración de accesorio inválida.')
        entrada, extremo, clase=puertos[puerto]
        nps=entrada if entrada is not None else c['nps']
        rating=clase if extremo=='flanged' else c['rating']
        if c['kind']=='tee' and c['branchNps']>nps:
            raise ValueError('La derivación de la tee no puede superar la medida de entrada.')
        salida=c['outNps'] if c['kind']=='reducer' else nps
        tipo_salida='flanged' if c['kind']=='valve' or c['kind']=='flange' and extremo!='flanged' else 'plain'
        if c['kind']!='cap':puertos[c['id']+':out']=(salida,tipo_salida,rating)
        if c['kind']=='tee':puertos[c['id']+':branch']=(c['branchNps'],'plain',rating)
        ids.add(c['id']);usados.add(puerto)
    return diseno


def materiales_piping(diseno):
    validar_piping(diseno)
    rows=OrderedDict();puertos={'origin':(None,'plain',None)}
    def agregar(tipo,nps,rating,salida=None,largo=0,detalle=''):
        nombre=TIPOS[tipo]
        if tipo=='elbow':nombre+=' '+str(int(detalle))+'°'
        if tipo=='reducer':nombre+=' '+('excéntrico' if detalle=='eccentric' else 'concéntrico')
        if tipo=='valve':nombre+=' '+('bola' if detalle=='ball' else 'compuerta')
        medida=MEDIDAS[nps]['label']+(' × '+MEDIDAS[salida]['label'] if salida is not None else '')
        clase=rating if tipo in ('flange','valve','cap') else '—'
        key=(nombre,medida,clase)
        if key not in rows:rows[key]={'description':nombre,'nps':medida,'rating':clase,'quantity':0,'lengthMM':0}
        rows[key]['quantity']+=1
        if tipo=='pipe':rows[key]['lengthMM']+=largo
    for c in diseno['components']:
        entrada,extremo,clase=puertos[c['parentPort']]
        nps=c['nps'] if entrada is None else entrada
        rating=clase if extremo=='flanged' else c['rating']
        adaptador=(c['kind'] not in ('flange','valve','cap') and extremo=='flanged') or (c['kind'] in ('valve','cap') and c['parentPort']!='origin' and extremo=='plain')
        if adaptador:agregar('flange',nps,rating)
        salida=c['outNps'] if c['kind']=='reducer' else c['branchNps'] if c['kind']=='tee' and c['branchNps']!=nps else None
        agregar(c['kind'],nps,rating,salida,c['lengthMM'],c['bendAngle'] if c['kind']=='elbow' else c['valveType'] if c['kind']=='valve' else c['reduction'])
        tipo='flanged' if c['kind']=='valve' or c['kind']=='flange' and extremo!='flanged' else 'plain'
        if c['kind']!='cap':puertos[c['id']+':out']=(c['outNps'] if c['kind']=='reducer' else nps,tipo,rating)
        if c['kind']=='tee':puertos[c['id']+':branch']=(c['branchNps'],'plain',rating)
    return list(rows.values())
