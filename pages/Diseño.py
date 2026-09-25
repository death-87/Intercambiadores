import streamlit as st
import json
import os
import streamlit.components.v1 as components

st.set_page_config(page_title="Editor 3D de Equipos", layout="wide")

# Rutas de carpetas y base de datos
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
DB_FILE = os.path.join(parent_dir, "equipos.json")

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

# Leer el parámetro enviado por URL (ej. ?equipo=C702)
params = st.query_params
equipo_url = params.get("equipo", None)

st.title("🛠️ Editor 3D de Intercambiadores de Calor")

# Barra superior de control (Seleccionar o Crear Nuevo)
col1, col2, col3 = st.columns([2, 2, 1])

lista_equipos = ["-- NUEVO EQUIPO (En blanco) --"] + list(db.keys())

# Determinar índice inicial basado en la URL
index_default = 0
if equipo_url and equipo_url in db:
    index_default = lista_equipos.index(equipo_url)

with col1:
    equipo_seleccionado = st.selectbox("Seleccionar Equipo:", lista_equipos, index=index_default)

# Si cambia el selectbox manualmente, actualizamos la URL
if equipo_seleccionado != "-- NUEVO EQUIPO (En blanco)--" and equipo_seleccionado != equipo_url:
    st.query_params["equipo"] = equipo_seleccionado
elif equipo_seleccionado == "-- NUEVO EQUIPO (En blanco) --" and "equipo" in params:
    st.query_params.clear()

nombre_default = "" if "NUEVO" in equipo_seleccionado else equipo_seleccionado

with col2:
    tag_guardar = st.text_input("TAG del Equipo (Ej: C702):", value=nombre_default)

with col3:
    st.write("") # Espaciador visual
    # Nota: El botón real de guardado está dentro del canvas 3D para capturar toda la data en tiempo real.
    st.info("💡 Usa el botón verde del menú flotante izquierdo en el 3D para guardar.")

# Plantilla inicial en blanco (4 boquillas por defecto sin texto)
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

# Obtener los datos a enviar al HTML
datos_actuales = plantilla_blanco if "NUEVO" in equipo_seleccionado or not equipo_seleccionado else db.get(equipo_seleccionado, plantilla_blanco)

# Cargar el componente 3D de la carpeta /visor_3d
component_path = os.path.join(parent_dir, "visor_3d")
visor_componente = components.declare_component("visor_3d", path=component_path)

# Renderizar el visor pasando los datos iniciales
resultado_guardar = visor_componente(datos_iniciales=datos_actuales, key=equipo_seleccionado)

# Procesar cuando se presiona "Guardar" en el HTML
if resultado_guardar is not None:
    tag_limpio = tag_guardar.strip()
    if not tag_limpio:
        st.error("⚠️ Error: Debes ingresar un TAG válido (Ej: C702) en la parte superior antes de guardar.")
    else:
        db[tag_limpio] = resultado_guardar
        guardar_db(db)
        st.success(f"✅ ¡Equipo '{tag_limpio}' guardado con éxito en la base de datos!")
        st.query_params["equipo"] = tag_limpio
        st.rerun()
