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
        with open(DB_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def guardar_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = cargar_db()

params = st.query_params
equipo_url = params.get("equipo", None)

st.title("🛠️ Editor 3D de Intercambiadores de Calor")

col1, col2, col3 = st.columns([2, 2, 1])

lista_equipos = ["-- NUEVO EQUIPO (En blanco) --"] + list(db.keys())

index_default = 0
if equipo_url and equipo_url in db:
    index_default = lista_equipos.index(equipo_url)

with col1:
    equipo_seleccionado = st.selectbox("Seleccionar Equipo:", lista_equipos, index=index_default)

if equipo_seleccionado != "-- NUEVO EQUIPO (En blanco) --" and equipo_seleccionado != equipo_url:
    st.query_params["equipo"] = equipo_seleccionado
elif equipo_seleccionado == "-- NUEVO EQUIPO (En blanco) --" and "equipo" in params:
    st.query_params.clear()

nombre_default = "" if "NUEVO" in equipo_seleccionado else equipo_seleccionado

with col2:
    tag_guardar = st.text_input("TAG del Equipo para Guardar (Ej: C702):", value=nombre_default)

with col3:
    st.write("")
    st.info("💡 Haz clic en el botón verde **💾 GUARDAR EQUIPO** dentro del visor 3D.")

plantilla_blanco = {
    "nameplate": "",
    "vent": "",
    "drain": "",
    "nozzles": [
        {"tagName": "", "diaIndex": 6, "rating": "150#", "bodyPart": "shell", "pos": "superior", "valX": -1.5, "hasNS": False, "tagNS": "", "hasFS": False, "tagFS": ""},
        {"tagName": "", "diaIndex": 6, "rating": "150#", "bodyPart": "shell", "pos": "inferior", "valX": 1.5, "hasNS": False, "tagNS": "", "hasFS": False, "tagFS": ""},
        {"tagName": "", "diaIndex": 6, "rating": "150#", "bodyPart": "channel", "pos": "superior", "valX": -2.9775, "hasNS": False, "tagNS": "", "hasFS": False, "tagFS": ""},
        {"tagName": "", "diaIndex": 6, "rating": "150#", "bodyPart": "channel", "pos": "inferior", "valX": -2.9775, "hasNS": False, "tagNS": "", "hasFS": False, "tagFS": ""}
    ]
}

datos_actuales = plantilla_blanco if "NUEVO" in equipo_seleccionado or not equipo_seleccionado else db.get(equipo_seleccionado, plantilla_blanco)

if os.path.exists(HTML_FILE):
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    json_data_str = json.dumps(datos_actuales)
    html_injectado = html_content.replace(
        "/*__INJECT_DATA_HERE__*/", 
        f"window.initialExchangerData = {json_data_str};"
    )
    
    # Captura el resultado cuando se presiona el botón en el 3D
    resultado_guardar = components.html(html_injectado, height=820, scrolling=False)
    
    if resultado_guardar is not None:
        tag_limpio = tag_guardar.strip()
        if not tag_limpio:
            st.error("⚠️ Error: Debes ingresar un TAG válido (Ej: C702) en la casilla superior antes de hacer clic en guardar.")
        else:
            db[tag_limpio] = resultado_guardar
            guardar_db(db)
            st.success(f"✅ ¡Equipo '{tag_limpio}' guardado exitosamente en la base de datos!")
            st.query_params["equipo"] = tag_limpio
            st.rerun()
else:
    st.error(f"No se encontró el archivo HTML en: {HTML_FILE}")
