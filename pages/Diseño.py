import streamlit as st
import json
import os
import streamlit.components.v1 as components

st.set_page_config(page_title="Editor 3D de Equipos", layout="wide")

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
DB_FILE = os.path.join(parent_dir, "equipos.json")
HTML_FILE = os.path.join(parent_dir, "visor_3d", "index.html")

def cargar_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def guardar_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

db = cargar_db()

params = st.query_params
equipo_url = params.get("equipo", None)

st.title("🛠️ Editor 3D de Intercambiadores de Calor")

col1, col2 = st.columns([3, 3])

lista_equipos = ["-- NUEVO EQUIPO (En blanco) --"] + list(db.keys())

index_default = 0
if equipo_url and equipo_url in db:
    index_default = lista_equipos.index(equipo_url)

with col1:
    equipo_seleccionado = st.selectbox("Seleccionar Equipo para Editar:", lista_equipos, index=index_default)

if equipo_seleccionado != "-- NUEVO EQUIPO (En blanco) --" and equipo_seleccionado != equipo_url:
    st.query_params["equipo"] = equipo_seleccionado
    st.rerun()
elif equipo_seleccionado == "-- NUEVO EQUIPO (En blanco) --" and "equipo" in params:
    st.query_params.clear()
    st.rerun()

nombre_default = "" if "NUEVO" in equipo_seleccionado else equipo_seleccionado

with col2:
    tag_input = st.text_input("TAG del Equipo (Ej: C702):", value=nombre_default)

plantilla_blanco = {
    "nameplate": tag_input if tag_input else "",
    "vent": "",
    "drain": "",
    "nozzles": [
        {"tagName": "S1", "diaIndex": 6, "rating": "300#", "bodyPart": "shell", "pos": "superior", "valX": -1.5, "hasNS": True, "tagNS": '3/4"', "hasFS": True, "tagFS": '1"'},
        {"tagName": "S2", "diaIndex": 6, "rating": "300#", "bodyPart": "shell", "pos": "inferior", "valX": 1.5, "hasNS": True, "tagNS": '3/4"', "hasFS": True, "tagFS": '1"'},
        {"tagName": "T1", "diaIndex": 8, "rating": "300#", "bodyPart": "channel", "pos": "superior", "valX": -2.9775, "hasNS": True, "tagNS": '1"', "hasFS": True, "tagFS": '1"'},
        {"tagName": "T2", "diaIndex": 8, "rating": "300#", "bodyPart": "channel", "pos": "inferior", "valX": -2.9775, "hasNS": True, "tagNS": '1"', "hasFS": True, "tagFS": '1"'}
    ]
}

datos_actuales = plantilla_blanco if "NUEVO" in equipo_seleccionado or not equipo_seleccionado else db.get(equipo_seleccionado, plantilla_blanco)

if tag_input:
    datos_actuales["nameplate"] = tag_input

# Capturar datos recibidos desde el visor 3D para persistencia
component_value = components.html(
    "", height=0
) # Inicializador pasivo

if os.path.exists(HTML_FILE):
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    json_data_str = json.dumps(datos_actuales)
    html_injectado = html_content.replace(
        "/*__INJECT_DATA_HERE__*/", 
        f"window.initialExchangerData = {json_data_str};"
    )
    
    # Capturar respuesta enviada por postMessage vía Streamlit Component
    res = components.html(html_injectado, height=750, scrolling=False)

    # Procesar guardado directo al presionar Guardar dentro del Visor HTML
    if "guardar_datos" in st.query_params:
        try:
            raw_json = st.query_params["guardar_datos"]
            datos_guardar = json.loads(raw_json)
            tag_equipo = datos_guardar.get("nameplate", "").strip()
            
            if tag_equipo:
                db[tag_equipo] = datos_guardar
                guardar_db(db)
                st.success(f"✅ ¡Equipo '{tag_equipo}' guardado exitosamente!")
                st.query_params["equipo"] = tag_equipo
                del st.query_params["guardar_datos"]
                st.rerun()
        except Exception as e:
            st.error(f"Error procesando el guardado: {e}")
