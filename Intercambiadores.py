import streamlit as st
import json
import os
import streamlit.components.v1 as components

st.set_page_config(page_title="Gestor de Intercambiadores", layout="wide")

current_dir = os.path.dirname(__file__)
DB_FILE = os.path.join(current_dir, "equipos.json")
HTML_FILE = os.path.join(current_dir, "visor_3d", "index.html")

def cargar_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

db = cargar_db()

st.title("🏭 Panel Principal - Intercambiadores de Calor")
st.markdown("Bienvenido al sistema de diseño paramétrico. Selecciona o edita tus equipos abajo.")

# Tabla interactiva con opción de ir al editor y indicador visual
st.subheader("📋 Lista de Equipos Registrados")

if not db:
    st.info("No hay equipos guardados todavía. Ve a la página de **Diseño** para crear uno nuevo.")
else:
    for tag, data in db.items():
        col_tag, col_status, col_btn = st.columns([2, 2, 2])
        with col_tag:
            st.write(f"**TAG:** {tag}")
        with col_status:
            st.markdown("Estado: **✅ Guardado y Validado**")
        with col_btn:
            if st.button(f"✏️ Editar {tag}", key=f"edit_{tag}"):
                st.switch_page("pages/diseno.py?equipo=" + tag)
        st.divider()

    # Sección inferior: Vista previa 3D limpia y sin panel de edición
    st.subheader("🔍 Vista Previa del Equipo Seleccionado (Solo Lectura)")
    tag_visualizar = st.selectbox("Selecciona un equipo para inspeccionar en 3D:", list(db.keys()))

    if tag_visualizar and os.path.exists(HTML_FILE):
        datos_equipo = db[tag_visualizar]
        
        with open(HTML_FILE, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Ocultar el panel de edición lateral CSS para dejarlo limpio y estético
        html_limpio = html_content.replace(
            "body { margin: 0; background: #111; color: #fff; font-family: sans-serif; overflow: hidden; }",
            "body { margin: 0; background: #111; color: #fff; font-family: sans-serif; overflow: hidden; } #ui-container { display: none !important; }"
        )
        
        json_data_str = json.dumps(datos_equipo)
        html_injectado = html_limpio.replace(
            "/*__INJECT_DATA_HERE__*/", 
            f"window.initialExchangerData = {json_data_str};"
        )
        
        # Renderizar visor limpio sin controles de edición
        components.html(html_injectado, height=600, scrolling=False)
