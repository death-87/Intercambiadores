"""Validación y materiales de diseños de piping. Longitudes en milímetros."""
from collections import OrderedDict
from pathlib import Path
import json
import math
import re
from piping_details import validar_detalles,REPAIRS

CATALOGO = json.loads((Path(__file__).parent / 'visor_piping' / 'catalogo.json').read_text())
MEDIDAS = {row['nps']: row for row in CATALOGO['items']}
TIPOS = {'pipe':'Tramo recto','poncho':'Poncho de refuerzo','sockolet':'Sockolet · SW','thredolet':'Thredolet · NPT','latrolet':'Latrolet · 45°','elbolet':'Elbolet', 'elbow':'Codo', 'tee':'Tee', 'reducer':'Reductor BW', 'valve':'Válvula', 'flange':'Brida WN', 'cap':'Brida ciega','gauge':'Manómetro'}
VALVULAS = {'gate':'compuerta','ball':'bola','globe':'globo','check':'retención','butterfly':'mariposa','psv':'PSV · seguridad','rv':'RV · alivio'}
OLETS = {'sockolet','thredolet','latrolet','elbolet','poncho'}
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
        if e.get('nameplate') is not None:
            if not isinstance(e['nameplate'],dict):raise ValueError('Nameplate inválido.')
            matrix=e['nameplate'].get('matrix')
            if not isinstance(matrix,list) or len(matrix)!=16 or any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>1e6 for x in matrix):raise ValueError('Posición de nameplate inválida.')
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


def conexion_piping(c,extremo,parent_kind=None):
    if c['kind']=='gauge' and (extremo!='threaded' or parent_kind!='pipe'):
        raise ValueError('El manómetro requiere un niple con salida NPT macho.')
    roscada=(c['kind']=='gauge' or c['kind']=='valve' and c.get('valveConnection')=='threaded' or
             c['kind']=='elbow' and c.get('outletEnd')=='threaded')
    entrada='threaded' if (c['kind']=='pipe' and (c.get('inletEnd')=='threaded' or c.get('inletEnd')!='welded' and extremo=='threaded')) or roscada else 'plain'
    if c['parentPort']!='origin':
        if extremo=='threaded' and entrada!='threaded':raise ValueError('El extremo NPT requiere un niple, un codo, una válvula roscada o un manómetro.')
        if extremo!='threaded' and entrada=='threaded':raise ValueError('Configura primero una salida roscada NPT en el componente anterior.')
        if extremo=='threaded' and (parent_kind=='pipe')==(c['kind']=='pipe'):raise ValueError('La unión NPT necesita una rosca macho y una hembra.')
    return entrada,roscada


def validar_elementos_externos(objetos):
    if not isinstance(objetos, list) or len(objetos) > 30:
        raise ValueError("Se admiten hasta 30 elementos externos.")
    ids = set()
    for objeto in objetos:
        if not isinstance(objeto, dict):
            raise ValueError("Elemento externo inválido.")
        identificador = objeto.get("id")
        tag = objeto.get("tag")
        if (
            not isinstance(identificador, str)
            or not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", identificador)
            or identificador in ids
            or objeto.get("kind") not in ("support", "tank")
            or not isinstance(tag, str)
            or not tag.strip()
            or len(tag) > 60
        ):
            raise ValueError("Identificación de elemento externo inválida.")
        ids.add(identificador)
        for campo, limite in (("position", 10_000_000), ("rotation", 360)):
            valores = objeto.get(campo)
            if not isinstance(valores, list) or len(valores) != 3 or any(
                type(valor) not in (int, float) or not -limite <= valor <= limite
                for valor in valores
            ):
                raise ValueError("Posición o rotación de elemento externo inválida.")
        for campo in ("a", "b", "height"):
            valor = objeto.get(campo)
            if type(valor) not in (int, float) or not 10 <= valor <= 100_000:
                raise ValueError("Las dimensiones del elemento externo deben estar entre 10 y 100.000 mm.")


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
        for key,limit in (('pipeXMM',100000),('pipeYMM',100000),('pipeZMM',100000),('pipeYawDeg',3600),('pipePitchDeg',90),('pipeCurveDeg',170),('pipeCurveRollDeg',3600)):
            value=c.get(key,0)
            if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>limit:raise ValueError('Ángulo del tramo inválido: '+key)
        for key in ('segmentBase','segmentGroup'):
            if key in c and (not isinstance(c[key],str) or len(c[key])>64):raise ValueError('Identificación de segmento inválida.')
        if 'hideInletWeld' in c and type(c['hideInletWeld']) is not bool:raise ValueError('Visibilidad de soldadura inválida.')
        if 'weldTag' in c and (not isinstance(c['weldTag'],str) or len(c['weldTag'])>40):raise ValueError('Identificación de soldadura inválida.')
        if c['kind']=='gauge' and 'gaugeDiameterMM' in c:
            diameter=c['gaugeDiameterMM']
            if type(diameter) not in (int,float) or not math.isfinite(diameter) or not 10<=diameter<=100000:
                raise ValueError('Diámetro exterior del manómetro inválido.')
        if type(c.get('bendAngle')) not in (int,float) or c['bendAngle'] not in (45,90) or c.get('reduction') not in ('concentric','eccentric') or c.get('valveType') not in VALVULAS or c.get('outletRating',c.get('rating')) not in CLASES:
            raise ValueError('Configuración de accesorio inválida.')
        if any(c.get(key,'welded') not in ('welded','flanged','threaded','vent45') for key in ('outletEnd','branchEnd')):raise ValueError('Terminación de extremo inválida.')
        if c.get('inletEnd','auto') not in ('auto','welded','threaded') or c.get('valveConnection','flanged') not in ('flanged','threaded') or c.get('outletEnd')=='threaded' and c['kind'] not in ('pipe','elbow') or c.get('branchEnd')=='threaded':raise ValueError('Tipo de conexión inválido.')
        if c.get('outletEnd')=='vent45' and c['kind']!='pipe' or c.get('branchEnd')=='vent45':
            raise ValueError('El corte de venteo solo se admite en la salida de un niple.')
        entrada, extremo, clase=puertos[puerto]
        parent_kind=next((x['kind'] for x in componentes if x['id']==puerto.split(':')[0]),None)
        inlet_type,roscada=conexion_piping(c,extremo,parent_kind)
        inlet_nps=entrada if entrada is not None else c['nps']
        if c.get('outletEnd')=='vent45' and c['lengthMM']<=MEDIDAS[inlet_nps]['odMM']/2:
            raise ValueError('El largo del niple de venteo debe superar el radio exterior.')
        nps=c.get('teeRunNps',inlet_nps) if c['kind']=='tee' and c.get('teeEntry')=='branch' else inlet_nps
        if c['kind']=='pipe' and c.get('pipeCurveDeg',0) and c['lengthMM']/(abs(c['pipeCurveDeg'])*math.pi/180)<=MEDIDAS[nps]['odMM']/2:raise ValueError('Radio de curvatura insuficiente.')
        if c['kind']=='tee' and (c.get('teeEntry','a') not in ('a','b','branch') or type(nps) not in (int,float) or nps not in MEDIDAS):raise ValueError('Entrada o medida principal de tee inválida.')
        rating=clase if extremo=='flanged' else c['rating']
        if c['kind']=='tee' and (inlet_nps if c.get('teeEntry')=='branch' else c['branchNps'])>nps:
            raise ValueError('La derivación de la tee no puede superar la medida de entrada.')
        if c['kind']=='elbolet':
            for key,limit in (('branchYawDeg',3600),('branchPitchDeg',90)):
                value=c.get(key,0)
                if type(value) not in (int,float) or not math.isfinite(value) or abs(value)>limit:raise ValueError('Giro de elbolet inválido.')
        if c['kind'] in OLETS:
            run=next(x for x in componentes if x['id']==puerto.split(':')[0])
            offset=c.get('tapOffsetMM')
            if (c['kind']=='elbolet')!=(run['kind']=='elbow') or c.get('branchAngle',45) not in (45,90) or c.get('branchDirection','outlet') not in ('inlet','outlet','+X','-X','+Y','-Y','+Z','-Z','custom') or type(offset) not in (int,float) or not math.isfinite(offset) or not 0<=offset<=(0 if run['kind']=='elbow' else run['lengthMM']) or c['outNps']>nps:raise ValueError('Posición o medida de sockolet inválida.')
        if c['kind']=='poncho':
            main_od,branch_od=MEDIDAS[nps]['odMM'],MEDIDAS[c['outNps']]['odMM']
            length,thickness,coverage=c.get('padLengthMM',max(250,branch_od*2)),c.get('padThicknessMM',6),c.get('padCoverageDeg',160)
            for name,value,minimum,maximum in (('largo',length,20,10000),('espesor',thickness,.5,100),('cobertura',coverage,10,170)):
                if type(value) not in (int,float) or not math.isfinite(value) or not minimum<=value<=maximum:raise ValueError('Dimensión de poncho inválida: '+name)
            if c['lengthMM']<=thickness+2:raise ValueError('La altura del ramal debe superar el espesor del poncho.')
            if length/2<=branch_od/2+2 or main_od/2*math.sin(coverage*math.pi/360)<=branch_od/2+2:raise ValueError('Amplía el largo o la cobertura del poncho para rodear el ramal.')
            if offset-length/2<-.001 or offset+length/2>run['lengthMM']+.001:raise ValueError('El poncho completo debe quedar dentro del tramo principal.')
        alivio=c['kind']=='valve' and c['valveType'] in ('psv','rv')
        salida=c['outNps'] if c['kind'] in ('reducer','sockolet','thredolet','latrolet','elbolet','poncho') or alivio else nps
        tipo_salida='threaded' if c['kind']=='thredolet' or roscada or c['kind']=='pipe' and c.get('outletEnd')=='threaded' else 'flanged' if c['kind'] in ('pipe','elbow','tee','reducer') and c.get('outletEnd')=='flanged' or c['kind']=='valve' or c['kind']=='flange' and extremo!='flanged' else 'plain'
        if c['kind'] not in ('cap','gauge') and c.get('outletEnd')!='vent45':puertos[c['id']+':out']=(salida,tipo_salida,c.get('outletRating',rating) if alivio else rating)
        if c['kind']=='tee':puertos[c['id']+':branch']=(nps if c.get('teeEntry')=='branch' else c['branchNps'],'flanged' if c.get('branchEnd')=='flanged' else 'plain',rating)
        if c['kind'] in ('pipe','elbow'):puertos[c['id']+':tap']=(nps,'run',rating)
        if c['kind'] in ('tee','pipe') and puerto=='origin':puertos[c['id']+':in']=(inlet_nps,'plain',rating)
        ids.add(c['id']);usados.add(puerto)
    validar_detalles(diseno)
    validar_elementos_externos(diseno.get('externalObjects', []))
    return diseno


def materiales_piping(diseno):
    validar_piping(diseno)
    rows=OrderedDict();puertos={'origin':(None,'plain',None),**validar_equipos(diseno)}
    def agregar(tipo,nps,rating,salida=None,largo=0,detalle='',terminacion=''):
        nombre=TIPOS[tipo]
        if tipo=='elbow':nombre+=' '+str(int(detalle))+'°'
        if tipo=='reducer':nombre+=' '+('excéntrico' if detalle=='eccentric' else 'concéntrico')
        if tipo=='valve':nombre+=' '+VALVULAS[detalle]
        nombre+=terminacion
        medida=MEDIDAS[nps]['label']+(' × '+MEDIDAS[salida]['label'] if salida is not None else '')
        clase=rating if rating=='NPT' or tipo in ('flange','valve','cap') else '—'
        key=(nombre,medida,clase)
        if key not in rows:rows[key]={'description':nombre,'nps':medida,'rating':clase,'quantity':0,'lengthMM':0}
        rows[key]['quantity']+=1
        if tipo=='pipe':rows[key]['lengthMM']+=largo
    for c in diseno['components']:
        entrada,extremo,clase=puertos[c['parentPort']]
        inlet_nps=c['nps'] if entrada is None else entrada
        nps=c.get('teeRunNps',inlet_nps) if c['kind']=='tee' and c.get('teeEntry')=='branch' else inlet_nps
        branch_nps=inlet_nps if c['kind']=='tee' and c.get('teeEntry')=='branch' else c['branchNps']
        rating=clase if extremo=='flanged' else c['rating']
        parent_kind=next((x['kind'] for x in diseno['components'] if x['id']==c['parentPort'].split(':')[0]),None)
        inlet_type,roscada=conexion_piping(c,extremo,parent_kind)
        adaptador=not roscada and ((c['kind'] not in ('flange','valve','cap') and extremo=='flanged') or (c['kind'] in ('valve','cap') and c['parentPort']!='origin' and extremo=='plain'))
        if adaptador:agregar('flange',inlet_nps,rating)
        if c['kind'] in ('pipe','elbow','tee','reducer') and c.get('outletEnd')=='flanged':agregar('flange',c['outNps'] if c['kind']=='reducer' else nps,rating)
        if c['kind']=='tee' and c.get('branchEnd')=='flanged':agregar('flange',nps if c.get('teeEntry')=='branch' else branch_nps,rating)
        alivio=c['kind']=='valve' and c['valveType'] in ('psv','rv')
        salida=c['outNps'] if c['kind'] in ('reducer','sockolet','thredolet','latrolet','elbolet','poncho') or alivio else branch_nps if c['kind']=='tee' and branch_nps!=nps else None
        end_thread=c['kind']=='pipe' and c.get('outletEnd')=='threaded'
        terminacion=' · roscado NPT hembra' if roscada and c['kind']=='elbow' else ' · roscada NPT' if roscada else ' · NPT '+('ambos extremos' if inlet_type=='threaded' and end_thread else 'entrada' if inlet_type=='threaded' else 'salida') if c['kind']=='pipe' and (inlet_type=='threaded' or end_thread) else ''
        if c['kind']=='gauge':terminacion=' · NPT hembra'
        if c.get('outletEnd')=='vent45':terminacion=' · venteo a 45°'+(' · entrada NPT macho' if inlet_type=='threaded' else '')
        if c['kind']=='poncho':
            terminacion+=' · L '+format(c.get('padLengthMM',max(250,MEDIDAS[c['outNps']]['odMM']*2)),'g')+' mm · e '+format(c.get('padThicknessMM',6),'g')+' mm · '+format(c.get('padCoverageDeg',160),'g')+'°'
        agregar(c['kind'],nps,'NPT' if roscada else rating+' / '+c.get('outletRating',rating) if alivio else rating,salida,c['lengthMM'],c['bendAngle'] if c['kind']=='elbow' else c['valveType'] if c['kind']=='valve' else c['reduction'],terminacion)
        tipo='threaded' if c['kind']=='thredolet' or roscada or end_thread else 'flanged' if c['kind'] in ('pipe','elbow','tee','reducer') and c.get('outletEnd')=='flanged' or c['kind']=='valve' or c['kind']=='flange' and extremo!='flanged' else 'plain'
        if c['kind'] not in ('cap','gauge') and c.get('outletEnd')!='vent45':puertos[c['id']+':out']=(c['outNps'] if c['kind'] in ('reducer','sockolet','thredolet','latrolet','elbolet','poncho') or alivio else nps,tipo,c.get('outletRating',rating) if alivio else rating)
        if c['kind']=='tee':puertos[c['id']+':branch']=(nps if c.get('teeEntry')=='branch' else c['branchNps'],'flanged' if c.get('branchEnd')=='flanged' else 'plain',rating)
        if c['kind'] in ('pipe','elbow'):puertos[c['id']+':tap']=(nps,'run',rating)
        if c['kind'] in ('tee','pipe') and c['parentPort']=='origin':puertos[c['id']+':in']=(inlet_nps,'plain',rating)
    output=list(rows.values())
    for repair in diseno.get('repairs',[]):
        host=next(c for c in diseno['components'] if c['id']==repair['hostId'])
        nps=puertos[host['id']+':out'][0]
        output.append({'description':REPAIRS[repair['type']]+' · '+repair['tag'],'nps':MEDIDAS[nps]['label']+' · e '+format(repair['thicknessMM'],'g')+' mm','rating':'—','quantity':1,'lengthMM':repair['lengthMM']})
    return output
