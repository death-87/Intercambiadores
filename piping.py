"""Piping e isométricos: diseño local y exportaciones, sin servicios externos."""
import base64
import hashlib
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
    rows=materiales_piping(diseno);data=[[p(x) for x in ['ELEMENTO','MEDIDA NPS','CLASE','CANTIDAD','LARGO TOTAL (mm)']]]+[[p(r['description']),p(r['nps']),p(r['rating']),p(r['quantity']),p(f"{r['lengthMM']:.1f}" if r['lengthMM'] else '—')] for r in rows]
    compact = len(rows)<=14
    if compact:
        small=ParagraphStyle('piping_small',parent=body,fontSize=7,leading=9)
        def compact_p(value):return Paragraph(escape(str(value)),small)
        data=[[compact_p(x) for x in ['ELEMENTO','NPS','CLASE','CANT.','LARGO (mm)']]]+[[compact_p(r['description']),compact_p(r['nps']),compact_p(r['rating']),compact_p(r['quantity']),compact_p(f"{r['lengthMM']:.1f}" if r['lengthMM'] else '—')] for r in rows]
    table=Table(data,colWidths=([34*mm,17*mm,12*mm,8*mm,15*mm] if compact else [100*mm,48*mm,30*mm,30*mm,55*mm]),repeatRows=1);table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5f1ee')),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#cbdde5')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    if compact:
        image._restrictSize(175*mm,135*mm)
        layout=Table([[image,'',table]],colWidths=[175*mm,6*mm,86*mm]);layout.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]));story.append(layout)
    else:
        story.extend([image,PageBreak(),Paragraph('Listado de materiales',title),table])
    story.extend([Spacer(1,3*mm),p('El listado incluye las bridas contraparte agregadas por el editor. Las válvulas se cuentan como conjuntos enflanchados.')])
    def pie(canvas,doc):
        canvas.saveState();canvas.setFont('Helvetica',7);canvas.setFillColor(colors.HexColor('#607c8e'));canvas.drawString(15*mm,8*mm,'Jndigital · '+datetime.now(ZoneInfo('America/Santiago')).strftime('%d-%m-%Y'));canvas.drawRightString(282*mm,8*mm,f'Página {doc.page}');canvas.restoreState()
    doc.build(story,onFirstPage=pie,onLaterPages=pie);return output.getvalue()


def mostrar_piping():
    from portal import ir_inicio
    st.markdown('''<style>[data-testid="stSidebar"],[data-testid="stSidebarNav"],[data-testid="collapsedControl"]{display:none}.jn-piping-head{padding:23px 27px;background:#102a3b;border-radius:14px;margin:12px 0 22px;color:white}.jn-piping-head small{color:#76d4bd;letter-spacing:1.5px;font-size:10px}.jn-piping-head h1{color:#f4f9fb;font-size:27px;margin:8px 0;padding:0}.jn-piping-head p{color:#acc5d3;font-size:12px;margin:0}</style>''',unsafe_allow_html=True)
    st.button('← Inicio de Jndigital',key='jn_piping_inicio',on_click=ir_inicio)
    st.markdown('''<header class="jn-piping-head"><small>JNDIGITAL / SOLUCIONES</small><h1>Piping e isométricos</h1><p>Conecta componentes, crea ramificaciones y prepara el isométrico de tu línea.</p></header>''',unsafe_allow_html=True)
    if 'jn_piping_load_token' not in st.session_state:st.session_state['jn_piping_load_token']='inicio'
    with st.expander('Abrir un diseño JSON respaldado'):
        upload=st.file_uploader('Diseño de piping',type=['json'],key='jn_piping_import')
        if st.button('Cargar este diseño',key='jn_piping_import_apply',disabled=upload is None):
            try:
                raw=upload.getvalue()
                if len(raw)>2_000_000:raise ValueError('El JSON supera 2 MB.')
                design=validar_piping(json.loads(raw));st.session_state['jn_piping_design']=design;st.session_state['jn_piping_import_sequence']=st.session_state.get('jn_piping_import_sequence',0)+1;st.session_state['jn_piping_load_token']=hashlib.sha256(raw).hexdigest()+':'+str(st.session_state['jn_piping_import_sequence']);st.session_state['jn_piping_imported']=True
            except (ValueError,TypeError,KeyError) as e:st.error(str(e))
    value=declarar_piping()(initial_data=st.session_state.get('jn_piping_design'),load_token=st.session_state['jn_piping_load_token'],imported=st.session_state.get('jn_piping_imported',False),height=940,key='jn_piping_editor',default=None)
    st.session_state['jn_piping_imported']=False
    if isinstance(value,dict) and value.get('token') == st.session_state['jn_piping_load_token'] and value.get('action') in ('update','export_pdf'):
        try:
            design=validar_piping(value.get('design'));st.session_state['jn_piping_design']=design
            if value['action']=='export_pdf':
                image=value.get('image','')
                if not isinstance(image,str) or not image.startswith('data:image/png;base64,') or len(image)>11_000_000:raise ValueError('Captura no válida.')
                content=base64.b64decode(image.split(',',1)[1],validate=True)
                fingerprint=hashlib.sha256(json.dumps(design,sort_keys=True).encode()+content).hexdigest()
                if st.session_state.get('jn_piping_capture_fingerprint')!=fingerprint:
                    st.session_state['jn_piping_pdf']=(hashlib.sha256(json.dumps(design,sort_keys=True).encode()).hexdigest(),pdf_piping(design,content));st.session_state['jn_piping_capture_fingerprint']=fingerprint
        except (ValueError,TypeError,KeyError) as e:st.error('No se pudo procesar el diseño: '+str(e))
    design=st.session_state.get('jn_piping_design')
    if design:
        name=re.sub(r'[^\w.-]+','_',design['title'])[:100] or 'Piping'
        prepared=st.session_state.get('jn_piping_pdf');digest=hashlib.sha256(json.dumps(design,sort_keys=True).encode()).hexdigest()
        if prepared and prepared[0]==digest:st.download_button('Descargar isométrico PDF',prepared[1],name+'.pdf','application/pdf',key='jn_piping_download_pdf',type='primary')
        elif prepared:st.caption('El diseño cambió. Pulsa «Isométrico PDF» en el editor para actualizar el documento.')
        rows=materiales_piping(design)
        if rows:
            st.subheader('Listado de materiales')
            frame=pd.DataFrame(rows).rename(columns={'description':'Elemento','nps':'Medida NPS','rating':'Clase','quantity':'Cantidad','lengthMM':'Largo total (mm)'})
            st.dataframe(frame,hide_index=True,use_container_width=True)
            st.download_button('Descargar materiales CSV',frame.to_csv(index=False).encode('utf-8-sig'),name+'_materiales.csv','text/csv',key='jn_piping_csv')
        st.download_button('Descargar respaldo JSON',json.dumps(design,ensure_ascii=False,indent=2).encode(),name+'.json','application/json',key='jn_piping_json')
    st.caption('El editor conserva un respaldo local en este navegador. Descarga el JSON para abrir el diseño en otro equipo. Los largos de accesorios y válvulas son configurables; bridas y diámetros usan el catálogo existente de Intercambiadores.')
