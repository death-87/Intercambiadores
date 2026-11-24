"""Piping e isométricos: diseño local y exportaciones, sin servicios externos."""
import base64
import hashlib
import uuid
import json
import re
from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo
from html import escape
import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape,A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle,PageBreak
from reportlab.lib.utils import ImageReader
from piping_core import validar_piping,materiales_piping
from visor_piping import declarar_piping


def pdf_piping(diseno,imagen):
    validar_piping(diseno)
    if not isinstance(imagen,bytes) or len(imagen)>8_000_000 or not imagen.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('La captura del isométrico no es válida.')
    reader=ImageReader(BytesIO(imagen));w,h=reader.getSize()
    if w*h>8_000_000:raise ValueError('La captura excede el tamaño admitido.')
    output=BytesIO();doc=SimpleDocTemplate(output,pagesize=landscape(A4),leftMargin=15*mm,rightMargin=15*mm,topMargin=13*mm,bottomMargin=15*mm,title=diseno['title'],author='Jndigital')
    styles=getSampleStyleSheet();body=ParagraphStyle('piping_body',parent=styles['Normal'],fontSize=8,leading=11,textColor=colors.HexColor('#244255'));title=ParagraphStyle('piping_title',parent=styles['Heading1'],fontSize=18,leading=22,textColor=colors.HexColor('#17394c'))
    def p(v):return Paragraph(escape(str(v)),body)
    story=[Paragraph('Jndigital · Piping e isométricos',title),p(diseno['title']),p('Vista isométrica · Longitudes en mm · Medidas nominales en pulgadas'),Spacer(1,4*mm)]
    image=Image(BytesIO(imagen),width=240*mm,height=240*mm*h/w);image._restrictSize(250*mm,135*mm)
    if diseno.get('equipments'):story.extend([p('Equipos: '+', '.join(e['tag'] for e in diseno['equipments'])),Spacer(1,2*mm)])
    rows=materiales_piping(diseno);data=[[p(x) for x in ['ELEMENTO','MEDIDA NPS','CLASE','CANTIDAD','LARGO TOTAL (mm)']]]+[[p(r['description']),p(r['nps']),p(r['rating']),p(r['quantity']),p(f"{r['lengthMM']:.1f}" if r['lengthMM'] else '—')] for r in rows]
    compact = len(rows)<=14
    if compact:
        small=ParagraphStyle('piping_small',parent=body,fontSize=7,leading=9)
        def compact_p(value):return Paragraph(escape(str(value)),small)
        data=[[compact_p(x) for x in ['ELEMENTO','NPS','CLASE','CANT.','LARGO (mm)']]]+[[compact_p(r['description']),compact_p(r['nps']),compact_p(r['rating']),compact_p(r['quantity']),compact_p(f"{r['lengthMM']:.1f}" if r['lengthMM'] else '—')] for r in rows]
    table=Table(data,colWidths=([34*mm,17*mm,12*mm,8*mm,15*mm] if compact else [100*mm,48*mm,30*mm,30*mm,55*mm]),repeatRows=1);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5f1ee')),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#cbdde5')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),3 if compact else 7),('RIGHTPADDING',(0,0),(-1,-1),3 if compact else 7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    if compact:
        image._restrictSize(175*mm,135*mm)
        layout=Table([[image,'',table]],colWidths=[175*mm,6*mm,86*mm]);layout.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]));story.append(layout)
    else:
        story.extend([image,PageBreak(),Paragraph('Listado de materiales',title),table])
    story.extend([Spacer(1,3*mm),p('El listado corresponde al piping e incluye las bridas contraparte. Las válvulas se cuentan como conjuntos enflanchados; no incluye materiales internos de los equipos.')])
    if diseno.get('repairs') or diseno.get('annotations'):
        story.extend([PageBreak(),Paragraph('Reparaciones y marcas de inspección',title)])
        if diseno.get('repairs'):
            from piping_details import REPAIRS
            hosts={c['id']:c['tag'] for c in diseno['components']}
            detail=[[p(x) for x in ['TAG','REPARACIÓN','TRAMO','POSICIÓN / DIMENSIONES','COMENTARIO']]]
            for repair in diseno['repairs']:
                dims=f"Inicio {repair['startMM']:g} mm · largo {repair['lengthMM']:g} mm · espesor {repair['thicknessMM']:g} mm"
                if repair['type']=='patch':dims+=f" · cobertura {repair['coverageDeg']:g}°"
                detail.append([p(repair['tag']),p(REPAIRS[repair['type']]),p(hosts[repair['hostId']]),p(dims),p(repair['comment'])])
            repairs_table=Table(detail,colWidths=[24*mm,44*mm,25*mm,76*mm,98*mm],repeatRows=1)
            repairs_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5f1ee')),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#cbdde5')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            story.extend([Paragraph('Registro de reparaciones',title),repairs_table,Spacer(1,5*mm)])
        if diseno.get('annotations'):
            hosts={c['id']:c['tag'] for c in diseno['components']};hosts.update({e['id']:e['tag'] for e in diseno.get('equipments',[])})
            detail=[[p(x) for x in ['REFERENCIA','ELEMENTO','COMENTARIO']]]+[[p(a['number']),p(hosts[a['hostId']]),p(a['text'])] for a in diseno['annotations']]
            marks_table=Table(detail,colWidths=[27*mm,45*mm,195*mm],repeatRows=1)
            marks_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5f1ee')),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#cbdde5')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            story.extend([Paragraph('Referencias del dibujo',title),marks_table])
    def pie(canvas,doc):
        canvas.saveState();canvas.setFont('Helvetica',7);canvas.setFillColor(colors.HexColor('#607c8e'));canvas.drawString(15*mm,8*mm,'Jndigital · '+datetime.now(ZoneInfo('America/Santiago')).strftime('%d-%m-%Y'));canvas.drawRightString(282*mm,8*mm,f'Página {doc.page}');canvas.restoreState()
    doc.build(story,onFirstPage=pie,onLaterPages=pie);return output.getvalue()


def mostrar_piping(validar_equipo=None):
    from portal import ir_inicio
    st.markdown('''<style>[data-testid="stSidebar"],[data-testid="stSidebarNav"],[data-testid="collapsedControl"]{display:none}.jn-piping-head{padding:23px 27px;background:#102a3b;border-radius:14px;margin:12px 0 22px;color:white}.jn-piping-head small{color:#76d4bd;letter-spacing:1.5px;font-size:10px}.jn-piping-head h1{color:#f4f9fb;font-size:27px;margin:8px 0;padding:0}.jn-piping-head p{color:#acc5d3;font-size:12px;margin:0}</style>''',unsafe_allow_html=True)
    st.button('← Inicio de Jndigital',key='jn_piping_inicio',on_click=ir_inicio)
    st.markdown('''<header class="jn-piping-head"><small>JNDIGITAL / SOLUCIONES</small><h1>Piping e isométricos</h1><p>Conecta líneas, válvulas y boquillas de equipos en un mismo ensamblaje.</p></header>''',unsafe_allow_html=True)
    if st.session_state.pop('jn_piping_go_assembly',False):st.session_state['jn_piping_mode']='Ensamblaje de piping'
    if st.session_state.pop('jn_piping_go_equipment',False):st.session_state['jn_piping_mode']='Herramientas de equipo'
    mode=st.radio('Área de trabajo',['Ensamblaje de piping','Herramientas de equipo'],horizontal=True,key='jn_piping_mode')
    if mode=='Herramientas de equipo':
        from piping_equipment import mostrar_herramientas_equipo
        mostrar_herramientas_equipo(validar_equipo)
        return
    if 'jn_piping_load_token' not in st.session_state:st.session_state['jn_piping_load_token']='inicio'
    from piping_r2 import mostrar_cuenta, guardar_proyecto
    project_config, project_authorized = mostrar_cuenta()
    with st.expander('Continuar un proyecto guardado en otro equipo'):
        upload=st.file_uploader('Diseño de piping',type=['json'],key='jn_piping_import')
        if st.button('Cargar este diseño',key='jn_piping_import_apply',disabled=upload is None):
            try:
                raw=upload.getvalue()
                if len(raw)>32_000_000:raise ValueError('El JSON supera 32 MB.')
                design=validar_piping(json.loads(raw));st.session_state.pop('jn_r2_target', None);st.session_state['jn_piping_design']=design;st.session_state['jn_piping_import_sequence']=st.session_state.get('jn_piping_import_sequence',0)+1;st.session_state['jn_piping_load_token']=hashlib.sha256(raw).hexdigest()+':'+str(st.session_state['jn_piping_import_sequence']);st.session_state['jn_piping_imported']=True
            except (ValueError,TypeError,KeyError) as e:st.error(str(e))
    target = st.session_state.get('jn_r2_target') if project_authorized else None
    value=declarar_piping()(initial_data=st.session_state.get('jn_piping_design'),load_token=st.session_state['jn_piping_load_token'],imported=st.session_state.get('jn_piping_imported',False),equipment_import=st.session_state.get('jn_piping_pending_equipment'),equipment_import_token=st.session_state.get('jn_piping_equipment_import_token'),project_cloud_ready=project_authorized, owner_exports=project_authorized, project_target={'name': target['name'], 'designId': target['design_id']} if target else None,project_ack=st.session_state.get('jn_project_ack'),height=940,key='jn_piping_editor',default=None)
    st.session_state['jn_piping_imported']=False
    if isinstance(value,dict) and value.get('token') == st.session_state['jn_piping_load_token'] and value.get('action') in ('update','export_pdf','equipment_applied','equipment_error','edit_equipment','save_project'):
        try:
            design=validar_piping(value.get('design'));st.session_state['jn_piping_design']=design
            if value['action']=='save_project' and value.get('eventId')!=st.session_state.get('jn_project_save_event'):
                st.session_state['jn_project_save_event']=value.get('eventId')
                try:
                    if not project_authorized:
                        raise ValueError('Solo el propietario puede guardar en la nube.')
                    overwrite = value.get('overwrite') is True
                    if overwrite and (not target or target['design_id'] != design['id']):
                        raise ValueError('Abre el archivo desde Mis diseños antes de sobrescribirlo.')
                    name = target['name'] if overwrite else value.get('projectName')
                    project = guardar_proyecto(project_config, value['eventId'], name, design, target if overwrite else None)
                    st.session_state['jn_r2_target'] = project
                    st.session_state['jn_project_ack'] = {'eventId': value['eventId'], 'ok': True, 'project': {'name': project['name']}, 'overwrite': overwrite}
                    st.session_state.pop('jn_r2_projects', None)
                except ValueError as error:st.session_state['jn_project_ack']={'eventId':value['eventId'],'ok':False,'error':str(error)}
                st.rerun()
            if value['action']=='edit_equipment' and value.get('eventId')!=st.session_state.get('jn_piping_edit_event'):
                equipment=next((e for e in design.get('equipments',[]) if e['id']==value.get('equipmentId')),None)
                if equipment is None:raise ValueError('Selecciona un equipo existente.')
                from piping_equipment import abrir_equipo
                abrir_equipo(equipment)
                st.session_state['piping_equipment_existing']=equipment['id']
                st.session_state['jn_piping_edit_event']=value['eventId']
                st.session_state['jn_piping_go_equipment']=True
                st.rerun()
            if value.get('equipmentApplied')==st.session_state.get('jn_piping_equipment_import_token') and value.get('equipmentApplied'):
                st.session_state.pop('jn_piping_pending_equipment',None);st.session_state.pop('jn_piping_equipment_import_token',None)
                if value['action']=='equipment_error':st.error('No se actualizó el equipo. Verifica que sus boquillas conectadas sigan existiendo; el ensamblaje anterior se conserva.')
            if value['action']=='export_pdf' and project_authorized:
                image=value.get('image','')
                if not isinstance(image,str) or not image.startswith('data:image/png;base64,') or len(image)>11_000_000:raise ValueError('Captura no válida.')
                content=base64.b64decode(image.split(',',1)[1],validate=True)
                fingerprint=hashlib.sha256(json.dumps(design,sort_keys=True).encode()+content).hexdigest()
                if st.session_state.get('jn_piping_capture_fingerprint')!=fingerprint:
                    st.session_state['jn_piping_pdf']=(hashlib.sha256(json.dumps(design,sort_keys=True).encode()).hexdigest(),pdf_piping(design,content));st.session_state['jn_piping_capture_fingerprint']=fingerprint
        except (ValueError,TypeError,KeyError) as e:st.error('No se pudo procesar el diseño: '+str(e))
    design=st.session_state.get('jn_piping_design')
    if design:
        for equipment in design.get('equipments',[]):
            for warning in equipment.get('warnings',[]):st.caption(equipment['tag']+' · '+warning)
        name=re.sub(r'[^\w.-]+','_',design['title'])[:100] or 'Piping'
        prepared=st.session_state.get('jn_piping_pdf');digest=hashlib.sha256(json.dumps(design,sort_keys=True).encode()).hexdigest()
        if project_authorized and prepared and prepared[0]==digest:st.download_button('Descargar isométrico PDF',prepared[1],name+'.pdf','application/pdf',key='jn_piping_download_pdf',type='primary')
        elif project_authorized and prepared:st.caption('El diseño cambió. Pulsa «Isométrico PDF» en el editor para actualizar el documento.')
        rows=materiales_piping(design)
        if rows:
            st.subheader('Listado de materiales')
            frame=pd.DataFrame(rows).rename(columns={'description':'Elemento','nps':'Medida NPS','rating':'Clase','quantity':'Cantidad','lengthMM':'Largo total (mm)'})
            st.dataframe(frame,hide_index=True,use_container_width=True)
            if project_authorized:
                st.download_button('Descargar materiales CSV',frame.to_csv(index=False).encode('utf-8-sig'),name+'_materiales.csv','text/csv',key='jn_piping_csv')
        st.download_button('Descargar respaldo JSON',json.dumps(design,ensure_ascii=False,indent=2).encode(),name+'.json','application/json',key='jn_piping_json')
    st.caption('Descarga el JSON para conservar tu diseño y volver a abrirlo en otro equipo. El propietario también puede guardar copias privadas en la nube. Los largos de accesorios y válvulas son configurables; bridas y diámetros usan el catálogo de Intercambiadores.')
