"""Reparaciones y marcas visuales guardadas dentro del proyecto de piping."""
import math
import re

REPAIRS={'type_b':'Camisa Tipo B · soldada','patch':'Parche soldado'}
COLORS={'#c74336','#276caa','#16846a','#d28a24'}


def validar_detalles(design):
    components={c['id']:c for c in design['components']};equipment={e['id'] for e in design.get('equipments',[])}
    def text(v,limit):return isinstance(v,str) and len(v)<=limit
    def numeric(v,low,high):return type(v) in (int,float) and math.isfinite(v) and low<=v<=high
    for key in ('repairs','annotations'):
        values=design.get(key,[])
        if not isinstance(values,list) or len(values)>100:raise ValueError('Se admiten hasta 100 reparaciones y 100 marcas.')
        ids=set()
        for value in values:
            if not isinstance(value,dict) or not isinstance(value.get('id'),str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',value['id']) or value['id'] in ids:raise ValueError('Identificación de reparación o marca inválida.')
            ids.add(value['id'])
            if key=='repairs':
                host=components.get(value.get('hostId'))
                if not host or host['kind']!='pipe' or value.get('type') not in REPAIRS or not text(value.get('tag'),40) or not text(value.get('comment'),500):raise ValueError('La reparación requiere un tramo recto.')
                for field,low,high in (('startMM',0,100000),('lengthMM',10,100000),('thicknessMM',.5,100),('coverageDeg',10,300),('rollDeg',-3600,3600)):
                    if not numeric(value.get(field),low,high):raise ValueError('Dimensión de reparación inválida: '+field)
                if 'color' in value and (not isinstance(value['color'], str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', value['color'])):
                    raise ValueError('Color de parche inválido.')
                if value['startMM']+value['lengthMM']>host['lengthMM']+.001:raise ValueError('La reparación debe quedar dentro del tramo.')
            else:
                if value.get('hostType') not in ('component','equipment') or value.get('hostId') not in (components if value['hostType']=='component' else equipment) or not text(value.get('number'),20) or not text(value.get('text'),500) or value.get('style') not in ('both','arrow','circle') or value.get('color') not in COLORS:raise ValueError('Marca o punto de referencia inválido.')
                point=value.get('coordinates')
                if not isinstance(point,list) or len(point)!=3 or not all(numeric(v,-1e6,1e6) for v in point):raise ValueError('Coordenadas de marca inválidas.')
                if not all(numeric(value.get(k),-800,800) for k in ('offsetX','offsetY')):raise ValueError('Desplazamiento de marca inválido.')
