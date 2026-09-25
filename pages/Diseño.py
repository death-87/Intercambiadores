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

col1, col2, col3 = st.columns([2, 2, 2])

lista_equipos = ["-- NUEVO EQUIPO (En blanco) --"] + list(db.keys())

index_default = 0
if equipo_url and equipo_url in db:
    index_default = lista_equipos.index(equipo_url)

with col1:
    equipo_seleccionado = st.selectbox("Seleccionar Equipo para Editar:", lista_equipos, index=index_default)

if equipo_seleccionado != "-- NUEVO EQUIPO (En blanco) --" and equipo_seleccionado != equipo_url:
    st.query_params["equipo"] = equipo_seleccionado
elif equipo_seleccionado == "-- NUEVO EQUIPO (En blanco) --" and "equipo" in params:
    st.query_params.clear()

nombre_default = "" if "NUEVO" in equipo_seleccionado else equipo_seleccionado

with col2:
    tag_input = st.text_input("TAG del Equipo (Ej: C702):", value=nombre_default)

plantilla_blanco = {
    "nameplate": tag_input if tag_input else "",
    "vent": "",
    "drain": "",
    "nozzles": [
        {"tagName": "S1", "diaIndex": 6, "rating": "300#", "bodyPart": "shell", "pos": "superior", "valX": -1.5, "hasNS": True, "tagNS": "3/4\"", "hasFS": True, "tagFS": "1\""},
        {"tagName": "S2", "diaIndex": 6, "rating": "300#", "bodyPart": "shell", "pos": "inferior", "valX": 1.5, "hasNS": True, "tagNS": "3/4\"", "hasFS": True, "tagFS": "1\""},
        {"tagName": "T1", "diaIndex": 8, "rating": "300#", "bodyPart": "channel", "pos": "superior", "valX": -2.9775, "hasNS": True, "tagNS": "1\"", "hasFS": True, "tagFS": "1\""},
        {"tagName": "T2", "diaIndex": 8, "rating": "300#", "bodyPart": "channel", "pos": "inferior", "valX": -2.9775, "hasNS": True, "tagNS": "1\"", "hasFS": True, "tagFS": "1\""}
    ]
}

# Obtener los datos actuales del equipo seleccionado
datos_actuales = plantilla_blanco if "NUEVO" in equipo_seleccionado or not equipo_seleccionado else db.get(equipo_seleccionado, plantilla_blanco)

with col3:
    st.markdown("###") # Espaciador vertical
    btn_guardar_streamlit = st.button("💾 Guardar Cambios en Base de Datos", type="primary", use_container_width=True)

if os.path.exists(HTML_FILE):
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    json_data_str = json.dumps(datos_actuales)
    
    # Inyectar los datos iniciales correctamente en el visor 3D
    html_injectado = html_content.replace(
        "/*__INJECT_DATA_HERE__*/", 
        f"window.initialExchangerData = {json_data_str};"
    )
    
    # Renderizar el visor 3D limpio (sin conflictos de retorno)
    components.html(html_injectado, height=820, scrolling=False)
    
    # Manejar el almacenamiento cuando se hace clic en el botón de Streamlit
    if btn_guardar_streamlit:
        tag_limpio = tag_input.strip()
        if not tag_limpio:
            st.error("⚠️ Por favor, ingresa un **TAG del Equipo** válido antes de guardar.")
        else:
            try:
                # Asegurar que se guarden datos limpios y serializables
                db[tag_limpio] = datos_actuales
                guardar_db(db)
                st.success(f"✅ ¡Equipo '{tag_limpio}' guardado exitosamente en la base de datos!")
                st.query_params["equipo"] = tag_limpio
            except Exception as e:
                st.error(f"❌ Error al guardar en la base de datos: {e}")
else:
    st.error(f"No se encontró el archivo HTML del visor en: {HTML_FILE}")
