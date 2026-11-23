"""Herramientas de intercambiadores dentro del ensamblaje, sin escritura en Sheets."""
import copy
import json
import uuid
import streamlit as st
from visor_3d import declarar_visor
from piping_core import validar_equipos


def nuevo_equipo(tag='E-101',vertical=True):
    return {'model':'J' if vertical else 'A','nameplate':tag,'dimensions':{'shellLength':3.0,'shellDiameter':1.0,'channelDiameter':1.0,'bonnetDiameter':1.0,'bonnetLength':.5,'channelLength':.5},'nozzles':[
        {'tagName':'N1','diaIndex':6,'rating':'150#','connectionType':'flanged','bodyPart':'bonnetLeft' if vertical else 'shell','pos':'axialMinus' if vertical else 'inferior','valX':0 if vertical else -1,'neckLength':.25},
        {'tagName':'N2','diaIndex':6,'rating':'150#','connectionType':'flanged','bodyPart':'bonnet' if vertical else 'shell','pos':'axialPlus' if vertical else 'superior','valX':0 if vertical else 1,'neckLength':.25}]}


def abrir_equipo(equipment):
    """Abre una copia editable sin alterar la posición del equipo en el ensamblaje."""
    st.session_state['jn_piping_equipment_draft']=copy.deepcopy(equipment['sourceDesign'])
    st.session_state['jn_piping_equipment_id']=equipment['id']
    st.session_state['jn_piping_equipment_selection']=uuid.uuid4().hex


def seleccionar_equipo():
    selected=st.session_state.get('piping_equipment_existing')
    equipment=next((e for e in st.session_state.get('jn_piping_design',{}).get('equipments',[]) if e['id']==selected),None)
    if equipment:abrir_equipo(equipment)


def mostrar_herramientas_equipo(validar_equipo):
    st.info('Diseña el equipo con las herramientas de Intercambiadores. «Usar este equipo en Piping» lo incorpora al ensamblaje con sus boquillas disponibles. No se guarda en Sheets.')
    equipments=st.session_state.get('jn_piping_design',{}).get('equipments',[])
    if equipments:
        ids=[None]+[e['id'] for e in equipments]
        if st.session_state.get('piping_equipment_existing') not in ids:st.session_state['piping_equipment_existing']=None
        st.selectbox('Equipo del ensamblaje · nameplate / TAG',ids,format_func=lambda id:next((e['tag'] for e in equipments if e['id']==id),'Seleccionar equipo…'),key='piping_equipment_existing',on_change=seleccionar_equipo)
    with st.expander('Nuevo equipo / abrir equipo existente',expanded='jn_piping_equipment_draft' not in st.session_state):
        tag=st.text_input('TAG del nuevo equipo',value='E-101',max_chars=80,key='piping_new_equipment_tag')
        vertical=st.checkbox('Equipo vertical',value=True,key='piping_new_vertical')
        if st.button('Crear equipo para este ensamblaje'):
            st.session_state['jn_piping_equipment_draft']=nuevo_equipo(tag.strip() or 'E-101',vertical)
            st.session_state['jn_piping_equipment_id']='e'+uuid.uuid4().hex
            st.session_state['jn_piping_equipment_selection']=uuid.uuid4().hex
        upload=st.file_uploader('Respaldo JSON de Intercambiadores',type=['json'],key='piping_equipment_upload')
        if st.button('Abrir respaldo del intercambiador',disabled=upload is None):
            try:
                if validar_equipo is None:raise ValueError('No está disponible el validador de equipos.')
                if upload.size>8_000_000:raise ValueError('El respaldo supera 8 MB.')
                draft=validar_equipo(json.loads(upload.getvalue()))
                if draft.get('stackedEquipment'):raise ValueError('Abre los equipos por separado para incorporar todas sus boquillas al ensamblaje.')
                st.session_state['jn_piping_equipment_draft']=draft;st.session_state['jn_piping_equipment_id']='e'+uuid.uuid4().hex;st.session_state['jn_piping_equipment_selection']=uuid.uuid4().hex
            except (ValueError,TypeError,KeyError) as e:st.error(str(e))
    draft=st.session_state.get('jn_piping_equipment_draft')
    if not draft:return
    st.subheader('Equipo en edición: '+(draft.get('nameplate') or 'Sin nameplate'))
    st.caption('Edita forma, tapas y boquillas. «Usar este equipo en Piping» actualiza el mismo equipo y conserva su ubicación y giro en el ensamblaje.')
    value=declarar_visor()(initial_data=draft,selected_tag=draft.get('nameplate'),selection_token=st.session_state['jn_piping_equipment_selection'],draft_key='PIPING_'+st.session_state['jn_piping_equipment_id'],piping_mode=True,piping_equipment_id=st.session_state['jn_piping_equipment_id'],readonly=False,height=1100,key='piping_equipment_builder',default=None)
    if not isinstance(value,dict) or value.get('builder_token')!=st.session_state['jn_piping_equipment_selection']:return
    if value.get('action')=='change' and value.get('data'):
        try:
            if validar_equipo:validar_equipo(value['data'])
            st.session_state['jn_piping_equipment_draft']=value['data']
        except (ValueError,TypeError,KeyError) as e:st.error(str(e))
    if value.get('action')=='piping_equipment' and value.get('event_id')!=st.session_state.get('jn_piping_equipment_event'):
        try:
            equipment=value['equipment']
            if equipment['id']!=st.session_state['jn_piping_equipment_id']:raise ValueError('El equipo no corresponde al editor activo.')
            validar_equipos({'equipments':[equipment]})
            if validar_equipo:validar_equipo(equipment['sourceDesign'])
            st.session_state['jn_piping_equipment_draft']=equipment['sourceDesign']
            st.session_state['jn_piping_pending_equipment']=equipment
            st.session_state['jn_piping_equipment_import_token']=uuid.uuid4().hex
            st.session_state['jn_piping_equipment_event']=value['event_id']
            st.session_state['jn_piping_go_assembly']=True
            st.rerun()
        except (ValueError,TypeError,KeyError) as e:st.error('No se pudo incorporar el equipo: '+str(e))
