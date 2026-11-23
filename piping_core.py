"""Validación y materiales de diseños de piping. Longitudes en milímetros."""
from collections import OrderedDict
from pathlib import Path
import json
import math
import re

CATALOGO = json.loads((Path(__file__).parent / 'visor_piping' / 'catalogo.json').read_text())
MEDIDAS = {row['nps']: row for row in CATALOGO['items']}
TIPOS = {'pipe':'Tramo recto','sockolet':'Sockolet · SW','thredolet':'Thredolet · NPT','latrolet':'Latrolet · 45°','elbolet':'Elbolet', 'elbow':'Codo', 'tee':'Tee', 'reducer':'Reductor', 'valve':'Válvula', 'flange':'Brida WN', 'cap':'Brida ciega'}
VALVULAS = {'gate':'compuerta','ball':'bola','globe':'globo','check':'retención','butterfly':'mariposa','psv':'PSV · seguridad','rv':'RV · alivio'}
OLETS = {'sockolet','thredolet','latrolet','elbolet'}
CLASES = {'150#','300#','600#'}


def validar_equipos(diseno):
    equipos=diseno.get('equipments',[])
    if equipos and len(json.dumps(diseno,ensure_ascii=False,separators=(',',':')))>30_000_000:raise ValueError('El ensamblaje supera el tamaño de respaldo admitido.')
    if not isinstance(equipos,list) or len(equipos)>6:raise ValueError('Se admiten hasta 6 equipos.')
    ids=set();puertos={}
    def vector(v):return isinstance(v,list) and len(v)==3 and all(type(x) in (int,float) and math.isfinite(x) and abs(x)<=1e6 for x in v)
    for e in equipos:
        if not isinstance(e,dict) or not isinstance(e.get('id'),str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',e['id']) or e['id'] in ids:raise ValueError('ID de equipo inválido.')
        ids.add(e['id'])
        if not isinstance(e.get('tag'),str) or not e['tag'].strip() or len(e['tag'])>80:raise ValueError('TAG de equipo inválido.')
        rotation=e.get('rotationDeg')
        if not vector(e.get('position')) or type(rotation) not in (int,float) or not math.isfinite(rotation) or abs(rotation)>3600:raise ValueError('Posición de equipo inválida.')
        asset=e.get('asset',{});data=asset.get('data',{})
        if asset.get('format')!='three-buffer-v1' or not isinstance(data.get('object'),dict) or len(json.dumps(asset))>16_000_000 or data.get('images') or data.get('textures'):raise ValueError('Geometría de equipo inválida.')
        if any(g.get('type')!='BufferGeometry' for g in data.get('geometries',[])) or any(m.get('type')!='MeshStandardMaterial' for m in data.get('materials',[])):raise ValueError('Geometría de equipo no admitida.')
        def object_valid(o,depth=0):
            if depth>60 or not isinstance(o,dict) or o.get('type') not in ('Group','Object3D','Mesh','InstancedMesh'):raise ValueError('Objeto de equipo inválido.')
            for child in o.get('children',[]):object_valid(child,depth+1)
        object_valid(data['object'])
        ports=e.get('ports');used=set()
        if not isinstance(ports,list) or len(ports)>200:raise ValueError('Boquillas inválidas.')
        for port in ports:
            if not isinstance(port,dict) or not isinstance(port.get('id'),str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',port['id']) or port['id'] in used:raise ValueError('Identidad de boquilla inválida.')
            used.add(port['id'])
            if not isinstance(port.get('tag'),str) or len(port['tag'])>80 or port.get('nps') not in MEDIDAS or port.get('rating') not in CLASES or not vector(port.get('position')) or not vector(port.get('axis')) or math.hypot(*port['axis'])<.01:raise ValueError('Conexión de boquilla inválida.')
            if port.get('flangeSpec'):
                f=port['flangeSpec']
                if any(type(f.get(k)) not in (int,float) or not math.isfinite(f[k]) or not 0<f[k]<=10000 for k in ('diameterMM','thicknessMM','hubDiameterMM','lengthMM','pitchMM','holeMM','odMM','raisedFaceMM')) or type(f.get('boltCount')) is not int or not 4<=f['boltCount']<=120:raise ValueError('Brida de equipo inválida.')
            puertos['eq-'+e['id']+'/'+port['id']]=(port['nps'],'flanged',port['rating'])
    return puertos


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
    for c in componentes:
        if isinstance(c,dict) and c.get('kind')=='latrolet' and any(isinstance(host,dict) and host.get('id')==str(c.get('parentPort','')).split(':')[0] and host.get('kind')=='elbow' for host in componentes):c['kind']='elbolet'
    ids, usados, puertos = set(), set(), {'origin':(None,'plain',None),**validar_equipos(diseno)}
    for c in componentes:
        if not isinstance(c,dict) or not isinstance(c.get('id'),str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',c['id']) or c['id'] in ids or c.get('kind') not in TIPOS:
            raise ValueError('Componente inválido o repetido.')
        puerto = c.get('parentPort')
        if not isinstance(puerto,str) or puerto not in puertos or (puerto in usados and not puerto.endswith(':tap')) or puerto.endswith(':tap')!=(c['kind'] in OLETS):
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
        if type(c.get('bendAngle')) not in (int,float) or c['bendAngle'] not in (45,90) or c.get('reduction') not in ('concentric','eccentric') or c.get('valveType') not in VALVULAS or c.get('outletRating',c.get('rating')) not in CLASES:
            raise ValueError('Configuración de accesorio inválida.')
        if any(c.get(key,'welded') not in ('welded','flanged') for key in ('outletEnd','branchEnd')):raise ValueError('Terminación de extremo inválida.')
        entrada, extremo, clase=puertos[puerto]
        if extremo=='threaded':raise ValueError('La salida NPT requiere un componente roscado, disponible en una próxima etapa.')
        nps=entrada if entrada is not None else c['nps']
        rating=clase if extremo=='flanged' else c['rating']
        if c['kind']=='tee' and c['branchNps']>nps:
            raise ValueError('La derivación de la tee no puede superar la medida de entrada.')
        if c['kind']=='elbolet':
            for key,limit in (('branchYawDeg',3600),('branchPitchDeg',90)):
                value=c.get(key,0)
                if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>limit:raise ValueError('Giro de elbolet inválido.')
        if c['kind'] in OLETS:
            run=next(x for x in componentes if x['id']==puerto.split(':')[0])
            offset=c.get('tapOffsetMM')
            if (c['kind']=='elbolet')!=(run['kind']=='elbow') or c.get('branchAngle',45) not in (45,90) or c.get('branchDirection','outlet') not in ('inlet','outlet','+X','-X','+Y','-Y','+Z','-Z','custom') or type(offset) not in (int,float) or not math.isfinite(offset) or not 0<=offset<=(0 if run['kind']=='elbow' else run['lengthMM']) or c['outNps']>nps:raise ValueError('Posición o medida de sockolet inválida.')
        alivio=c['kind']=='valve' and c['valveType'] in ('psv','rv')
        salida=c['outNps'] if c['kind'] in ('reducer','sockolet','thredolet','latrolet','elbolet') or alivio else nps
        tipo_salida='threaded' if c['kind']=='thredolet' else 'flanged' if c['kind'] in ('pipe','elbow','tee','reducer') and c.get('outletEnd')=='flanged' or c['kind']=='valve' or c['kind']=='flange' and extremo!='flanged' else 'plain'
        if c['kind']!='cap':puertos[c['id']+':out']=(salida,tipo_salida,c.get('outletRating',rating) if alivio else rating)
        if c['kind']=='tee':puertos[c['id']+':branch']=(c['branchNps'],'flanged' if c.get('branchEnd')=='flanged' else 'plain',rating)
        if c['kind'] in ('pipe','elbow'):puertos[c['id']+':tap']=(nps,'run',rating)
        ids.add(c['id']);usados.add(puerto)
    return diseno


def materiales_piping(diseno):
    validar_piping(diseno)
    rows=OrderedDict();puertos={'origin':(None,'plain',None),**validar_equipos(diseno)}
    def agregar(tipo,nps,rating,salida=None,largo=0,detalle=''):
        nombre=TIPOS[tipo]
        if tipo=='elbow':nombre+=' '+str(int(detalle))+'°'
        if tipo=='reducer':nombre+=' '+('excéntrico' if detalle=='eccentric' else 'concéntrico')
        if tipo=='valve':nombre+=' '+VALVULAS[detalle]
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
        if c['kind'] in ('pipe','elbow','tee','reducer') and c.get('outletEnd')=='flanged':agregar('flange',c['outNps'] if c['kind']=='reducer' else nps,rating)
        if c['kind']=='tee' and c.get('branchEnd')=='flanged':agregar('flange',c['branchNps'],rating)
        alivio=c['kind']=='valve' and c['valveType'] in ('psv','rv')
        salida=c['outNps'] if c['kind'] in ('reducer','sockolet','thredolet','latrolet','elbolet') or alivio else c['branchNps'] if c['kind']=='tee' and c['branchNps']!=nps else None
        agregar(c['kind'],nps,rating+' / '+c.get('outletRating',rating) if alivio else rating,salida,c['lengthMM'],c['bendAngle'] if c['kind']=='elbow' else c['valveType'] if c['kind']=='valve' else c['reduction'])
        tipo='threaded' if c['kind']=='thredolet' else 'flanged' if c['kind'] in ('pipe','elbow','tee','reducer') and c.get('outletEnd')=='flanged' or c['kind']=='valve' or c['kind']=='flange' and extremo!='flanged' else 'plain'
        if c['kind']!='cap':puertos[c['id']+':out']=(c['outNps'] if c['kind'] in ('reducer','sockolet','thredolet','latrolet','elbolet') or alivio else nps,tipo,c.get('outletRating',rating) if alivio else rating)
        if c['kind']=='tee':puertos[c['id']+':branch']=(c['branchNps'],'flanged' if c.get('branchEnd')=='flanged' else 'plain',rating)
        if c['kind'] in ('pipe','elbow'):puertos[c['id']+':tap']=(nps,'run',rating)
    return list(rows.values())
