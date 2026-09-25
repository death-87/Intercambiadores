import streamlit as st
import json
import os
import requests
import pandas as pd
import urllib.parse
import streamlit.components.v1 as components

st.set_page_config(page_title="Editor 3D de Equipos", layout="wide")

# =====================================================================
# 🔗 CONFIGURACIÓN DE CONEXIÓN A GOOGLE SHEETS
# =====================================================================
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxPmdGXS7i61XrwRDWc9rRJAceBByb4AmXt1Fzyrbuf2sEvvWMTuOw1iltTdXJ2mfhdSQ/exec"

SHEET_ID = "1lhpb211bqPyDAxxnBFgKaN7nY-WImR961xJ3mrIGYZ4"
HOJA_3D = "Diseño3D"
# =====================================================================

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
HTML_FILE = os.path.join(parent_dir, "visor_3d", "index.html")

@st.cache_data(ttl=0)
def cargar_db():
    """Lee la pestaña Diseño3D de Google Sheets y la convierte en diccionario."""
    try:
        hoja_encoded = urllib.parse.quote(HOJA_3D)
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={hoja_encoded}"
        df = pd.read_csv(url)
        
        db = {}
        if not df.empty and len(df.columns) >= 2:
            for _, row in df.iterrows():
                tag = str(row.iloc[0]).strip()
                datos_str = str(row.iloc[1]).strip()
                if tag and tag != 'nan' and datos_str != 'nan':
                    try:
                        db[tag] = json.loads(datos_str)
                    except json.JSONDecodeError:
                        pass
        return db
    except Exception:
        return {}

def guardar_db(tag, datos):
    payload = {
        "tag": tag,
        "datos": json.dumps(datos, ensure_ascii=False)
    }
    try:
        respuesta = requests.post(WEBAPP_URL, json=payload)
        return respuesta.status_code == 200
    except Exception as e:
        st.error(f"Error de conexión con Google Sheets: {e}")
        return False

db = cargar_db()

st.title("🛠️ Editor 3D de Intercambiadores de Calor")

col1, col2 = st.columns([3, 3])

lista_equipos = ["-- NUEVO EQUIPO (En blanco) --"] + sorted(list(db.keys()))

params = st.query_params
equipo_url = params.get("equipo", None)

index_default = 0
if equipo_url and equipo_url in db:
    index_default = lista_equipos.index(equipo_url)

with col1:
    equipo_seleccionado = st.selectbox("Seleccionar Equipo para Editar:", lista_equipos, index=index_default, key="select_equipo")

if equipo_seleccionado != "-- NUEVO EQUIPO (En blanco) --" and equipo_seleccionado != equipo_url:
    st.query_params["equipo"] = equipo_seleccionado
    st.rerun()
elif equipo_seleccionado == "-- NUEVO EQUIPO (En blanco) --" and "equipo" in params:
    st.query_params.clear()
    st.rerun()

# Plantilla base en caso de ser nuevo
plantilla_blanco = {
    "nameplate": "",
    "vent": '3/4"',
    "drain": '3/4"',
    "nozzles": [
        {"tagName": "S1", "diaIndex": 6, "rating": "300#", "bodyPart": "shell", "pos": "superior", "valX": -1.5, "hasNS": True, "tagNS": '3/4"', "hasFS": True, "tagFS": '1"'},
        {"tagName": "S2", "diaIndex": 6, "rating": "300#", "bodyPart": "shell", "pos": "inferior", "valX": 1.5, "hasNS": True, "tagNS": '3/4"', "hasFS": True, "tagFS": '1"'},
        {"tagName": "T1", "diaIndex": 8, "rating": "300#", "bodyPart": "channel", "pos": "superior", "valX": -2.9775, "hasNS": True, "tagNS": '1"', "hasFS": True, "tagFS": '1"'},
        {"tagName": "T2", "diaIndex": 8, "rating": "300#", "bodyPart": "channel", "pos": "inferior", "valX": -2.9775, "hasNS": True, "tagNS": '1"', "hasFS": True, "tagFS": '1"'}
    ]
}

# Seleccionar datos de la base de datos o plantilla
if equipo_seleccionado != "-- NUEVO EQUIPO (En blanco) --":
    datos_actuales = db.get(equipo_seleccionado, plantilla_blanco)
else:
    datos_actuales = plantilla_blanco

with col2:
    nombre_default = datos_actuales.get("nameplate", "") if equipo_seleccionado != "-- NUEVO EQUIPO (En blanco) --" else ""
    tag_input_streamlit = st.text_input("TAG / Nameplate del Equipo:", value=nombre_default, key="input_nameplate")

js_listener = """
<script>
window.addEventListener('message', function(event) {
    if (event.data && event.data.type === 'UPDATE_EXCHANGER_DATA') {
        const payload = JSON.stringify(event.data.payload);
        window.parent.postMessage({type: 'streamlit:setComponentValue', value: payload}, '*');
    }
});
</script>
"""

st.markdown("---")

if os.path.exists(HTML_FILE):
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Aseguramos que el nameplate actual de Streamlit se inyecte correctamente
    datos_actuales["nameplate"] = tag_input_streamlit if tag_input_streamlit else equipo_seleccionado
    
    json_data_str = json.dumps(datos_actuales)
    html_injectado = html_content.replace(
        "/*__INJECT_DATA_HERE__*/", 
        f"window.initialExchangerData = {json_data_str};"
    )
    
    # 🔑 CLAVE: Usamos un 'key' dinámico basado en el equipo seleccionado. 
    # Esto obliga a Streamlit a destruir y recrear el componente HTML por completo cada vez que cambias de equipo, 
    # cargando sus boquillas, diámetros y plugs reales desde cero.
    component_value = components.html(js_listener + html_injectado, height=720, scrolling=False, key=f"html_visor_{equipo_seleccionado}")
    
    # Guardamos cambios temporales en session_state ante modificaciones en el 3D
    if "working_data" not in st.session_state or st.session_state.get("current_loaded") != equipo_seleccionado:
        st.session_state.working_data = json.loads(json.dumps(datos_actuales))
        st.session_state.current_loaded = equipo_seleccionado

    if component_value:
        try:
            parsed_data = json.loads(component_value)
            st.session_state.working_data = parsed_data
            st.session_state.working_data["nameplate"] = tag_input_streamlit
        except Exception:
            pass
else:
    st.error(f"⚠️ No se encontró el visor HTML en: {HTML_FILE}")

st.markdown("---")
col_guardar, _ = st.columns([2, 4])
with col_guardar:
    if st.button("💾 GUARDAR EQUIPO EN SHEETS", type="primary", use_container_width=True):
        tag_final = tag_input_streamlit.strip() 
        
        if tag_final:
            # Asegurar que el nameplate final y los datos del 3D se guarden unidos
            if "working_data" in st.session_state:
                datos_a_guardar = st.session_state.working_data
            else:
                datos_a_guardar = datos_actuales
                
            datos_a_guardar["nameplate"] = tag_final
            
            with st.spinner('Guardando en la nube...'):
                exito = guardar_db(tag_final, datos_a_guardar)
            
            if exito:
                cargar_db.clear()
                st.success(f"✅ ¡Equipo '{tag_final}' guardado exitosamente con todas sus boquillas y plugs en Google Sheets!")
                st.query_params["equipo"] = tag_final
                st.rerun()
            else:
                st.error("❌ Ocurrió un problema al intentar guardar los datos.")
        else:
            st.warning("⚠️ Debes ingresar el TAG / Nameplate en el campo de texto superior para poder guardar.")
