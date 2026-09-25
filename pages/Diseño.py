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

st.title("🛠️ Editor 3D de Intercambiadores de Calor")

col1, col2 = st.columns([3, 3])

lista_equipos = ["-- NUEVO EQUIPO (En blanco) --"] + list(db.keys())

params = st.query_params
equipo_url = params.get("equipo", None)

index_default = 0
if equipo_url and equipo_url in db:
    index_default = lista_equipos.index(equipo_url)

with col1:
    equipo_seleccionado = st.selectbox("Seleccionar Equipo para Editar:", lista_equipos, index=index_default)

if equipo_seleccionado != "-- NUEVO EQUIPO (En blanco) --" and equipo_seleccionado != equipo_url:
    st.query_params["equipo"] = equipo_seleccionado
    if "current_editor_data" in st.session_state:
        del st.session_state["current_editor_data"]
    st.rerun()
elif equipo_seleccionado == "-- NUEVO EQUIPO (En blanco) --" and "equipo" in params:
    st.query_params.clear()
    if "current_editor_data" in st.session_state:
        del st.session_state["current_editor_data"]
    st.rerun()

nombre_default = "" if "NUEVO" in equipo_seleccionado else equipo_seleccionado

with col2:
    tag_input = st.text_input("TAG / Nameplate del Equipo (Ej: E-101):", value=nombre_default)

plantilla_blanco = {
    "nameplate": tag_input if tag_input else "",
    "vent": '3/4"',
    "drain": '3/4"',
    "nozzles": [
        {"tagName": "S1", "diaIndex": 6, "rating": "300#", "bodyPart": "shell", "pos": "superior", "valX": -1.5, "hasNS": True, "tagNS": '3/4"', "hasFS": True, "tagFS": '1"'},
        {"tagName": "S2", "diaIndex": 6, "rating": "300#", "bodyPart": "shell", "pos": "inferior", "valX": 1.5, "hasNS": True, "tagNS": '3/4"', "hasFS": True, "tagFS": '1"'},
        {"tagName": "T1", "diaIndex": 8, "rating": "300#", "bodyPart": "channel", "pos": "superior", "valX": -2.9775, "hasNS": True, "tagNS": '1"', "hasFS": True, "tagFS": '1"'},
        {"tagName": "T2", "diaIndex": 8, "rating": "300#", "bodyPart": "channel", "pos": "inferior", "valX": -2.9775, "hasNS": True, "tagNS": '1"', "hasFS": True, "tagFS": '1"'}
    ]
}

datos_actuales = db.get(equipo_seleccionado, plantilla_blanco) if equipo_seleccionado != "-- NUEVO EQUIPO (En blanco) --" else plantilla_blanco

if tag_input:
    datos_actuales["nameplate"] = tag_input

if "current_editor_data" not in st.session_state or st.session_state.get("last_selected") != equipo_seleccionado:
    st.session_state.current_editor_data = datos_actuales
    st.session_state.last_selected = equipo_seleccionado

st.markdown("---")
col_guardar, _ = st.columns([2, 4])
with col_guardar:
    if st.button("💾 GUARDAR EQUIPO EN JSON", type="primary", use_container_width=True):
        tag_final = tag_input.strip()
        if tag_final:
            data_to_save = st.session_state.get("current_editor_data", datos_actuales)
            data_to_save["nameplate"] = tag_final
            db[tag_final] = data_to_save
            guardar_db(db)
            st.success(f"✅ ¡Equipo '{tag_final}' guardado exitosamente con todas sus medidas!")
            st.query_params["equipo"] = tag_final
            st.rerun()
        else:
            st.warning("⚠️ Debes ingresar un TAG / Nameplate válido para poder guardar.")

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

if os.path.exists(HTML_FILE):
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    json_data_str = json.dumps(st.session_state.current_editor_data)
    html_injectado = html_content.replace(
        "/*__INJECT_DATA_HERE__*/", 
        f"window.initialExchangerData = {json_data_str};"
    )
    
    component_value = components.html(js_listener + html_injectado, height=720, scrolling=False)
    
    if component_value:
        try:
            parsed_data = json.loads(component_value)
            st.session_state.current_editor_data = parsed_data
        except Exception:
            pass
else:
    st.error(f"⚠️ No se encontró el visor HTML en: {HTML_FILE}")
