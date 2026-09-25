import streamlit as st
import json
import os
import streamlit.components.v1 as components

st.set_page_config(page_title="Diseño de Equipo", layout="wide")

# Rutas de carpetas
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
DB_FILE = os.path.join(parent_dir, "equipos.json")

# 1. Funciones de Base de Datos
def cargar_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def guardar_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = cargar_db()

# 2. Inicializar el Componente 3D (apunta a la carpeta /visor_3d)
component_path = os.path.join(parent_dir, "visor_3d")
visor_componente = components.declare_component("visor_3d", path=component_path)

# 3. Interfaz de Streamlit
st.title("Gestor de Intercambiadores de Calor")

# Lista para el selector
lista_equipos = ["-- NUEVO EQUIPO (Plantilla en blanco) --"] + list(db.keys())

col1, col2 = st.columns([3, 1])
with col1:
    equipo_seleccionado = st.selectbox("Selecciona un Equipo Guardado o crea uno Nuevo:", lista_equipos)

# Manejar el nombre por defecto para guardar
nombre_default = "" if "-- NUEVO" in equipo_seleccionado else equipo_seleccionado

with col2:
    nombre_guardar = st.text_input("TAG para Guardar (Ej: C702):", value=nombre_default)

# Plantilla base (4 boquillas por defecto, totalmente en blanco)
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

# Determinar qué datos enviar al HTML
datos_actuales = plantilla_blanco if "-- NUEVO" in equipo_seleccionado else db[equipo_seleccionado]

# 4. Mostrar el Componente 3D y capturar cuando el usuario presione "Guardar" en el HTML
nuevos_datos = visor_componente(datos_iniciales=datos_actuales, key=equipo_seleccionado)

# 5. Lógica de Guardado (Recibe la señal desde Javascript)
if nuevos_datos is not None:
    if nombre_guardar.strip() == "":
        st.error("⚠️ Debes ponerle un nombre al TAG (Ej: C702) antes de guardar.")
    else:
        db[nombre_guardar.strip()] = nuevos_datos
        guardar_db(db)
        st.success(f"✅ Equipo '{nombre_guardar.strip()}' guardado correctamente.")
        st.rerun() # Recargar para que aparezca en el selectbox
