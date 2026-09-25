import os
import streamlit as st
import streamlit.components.v1 as components

# Configuración de la página
st.set_page_config(
    page_title="Visor 3D Intercambiador", 
    layout="wide"
)

st.title("Visor 3D - Intercambiador de Calor")

# 1. Obtener la ruta de la carpeta actual ('pages')
current_dir = os.path.dirname(__file__)

# 2. Subir un nivel para llegar a la carpeta principal del proyecto
root_dir = os.path.dirname(current_dir)

# 3. Unir la ruta con el nombre del archivo HTML
html_file_path = os.path.join(root_dir, "intercambiador.html")

# Leer y renderizar el HTML
try:
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_code = f.read()
        
    # Renderizar el HTML
    # height=850 asegura que se vea completo sin necesidad de hacer scroll interno
    components.html(html_code, height=850, scrolling=False)

except FileNotFoundError:
    st.error(f"No se encontró el archivo HTML en la ruta: {html_file_path}. Asegúrate de que esté en la carpeta principal.")