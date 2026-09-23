import os
import re
import json
import base64
import requests
import urllib.parse
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Configuración de página de Streamlit
st.set_page_config(page_title="Diseño de Intercambiador de Calor", layout="wide")

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE GOOGLE DRIVE Y GOOGLE SHEETS
# -----------------------------------------------------------------------------
SHEET_ID = "1lhpb211bqPyDAxxnBFgKaN7nY-WImR961xJ3mrIGYZ4"
NOMBRE_HOJA = "Hoja 1"

GDRIVE_FOLDER_ID = "10hv3MlaXaL4rZkQrssnROAX18ms_31rc"
GDRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/10hv3MlaXaL4rZkQrssnROAX18ms_31rc"

# OPCIÓN B: Reemplaza las comillas con la URL que te genera al Desplegar como Aplicación Web (/exec)
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxKabZkU0Ri_SD4oIA3reQW4HAQI52hHvVAaeEPn5nosdicBwmxN_3tBfdqbNMFUT9Kow/exec"

# -----------------------------------------------------------------------------
# CARGA DE EQUIPOS DESDE GOOGLE SHEETS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def cargar_lista_equipos():
    try:
        nombre_hoja_encoded = urllib.parse.quote(NOMBRE_HOJA)
        sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_hoja_encoded}"
        data = pd.read_csv(sheet_url)
        col_eq = next((c for c in data.columns if 'EQUIPO' in str(c).upper()), None)
        if col_eq:
            equipos = sorted([str(x).strip() for x in data[col_eq].dropna().unique() if str(x).strip() not in ['', 'nan', 'Sin información']])
            return equipos
    except Exception:
        pass
    return ["E-101", "E-102", "E-103", "E-201"]

lista_equipos = cargar_lista_equipos()

# -----------------------------------------------------------------------------
# GENERADOR VECTORIAL SVG DEL INTERCAMBIADOR (HEIGHT=470, CY=180)
# -----------------------------------------------------------------------------
def generate_modular_exchanger_svg(config, selected_id=None):
    width, height = 1000, 470
    cy = 180  # Eje central elevado
    
    seq = config.get("components", {}).get("sequence", ["CHANNEL", "SHELL", "BONNET"])
    comp_lens = {
        "CHANNEL": float(config.get("components", {}).get("channel_length", 150)),
        "SHELL": float(config.get("components", {}).get("shell_length", 420)),
        "BONNET": float(config.get("components", {}).get("bonnet_length", 100))
    }
    
    total_len = sum(comp_lens.get(c, 100) for c in seq)
    scale = 650.0 / max(total_len, 1.0)
    
    r_shell = 85.0
    r_bonnet = 85.0
    
    coords = {}
    curr_x = 180.0
    
    for comp in seq:
        w_scaled = comp_lens.get(comp, 100) * scale
        coords[comp] = {"start": curr_x, "end": curr_x + w_scaled, "width": w_scaled}
        curr_x += w_scaled + 10.0
        
    svg_lines = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        '<style>',
        '  .axis { stroke: #ef4444; stroke-width: 2; stroke-dasharray: 8, 4; }',
        '  .body { fill: #f1f5f9; stroke: #334155; stroke-width: 2.5; }',
        '  .flange { fill: #475569; stroke: #1e293b; stroke-width: 2; }',
        '  .saddle { fill: #64748b; stroke: #0f172a; stroke-width: 2; }',
        '  .nozzle { fill: #cbd5e1; stroke: #1e293b; stroke-width: 2; }',
        '  .text-label { font-family: Arial, sans-serif; font-size: 13px; font-weight: bold; fill: #0f172a; text-anchor: middle; }',
        '  .sub-text { font-family: Arial, sans-serif; font-size: 10px; fill: #475569; text-anchor: middle; }',
        '</style>',
        f'<line x1="50" y1="{cy}" x2="{curr_x + 50}" y2="{cy}" class="axis" />'
    ]
    
    # Soportes (Saddles)
    shell_info = coords.get("SHELL", {"start": 200, "width": 300})
    for sad in config.get("saddles", []):
        sad_ratio = float(sad.get("position_ratio", 0.5))
        sad_x = shell_info["start"] + shell_info["width"] * sad_ratio
        svg_lines.append(f'<rect x="{sad_x - 18}" y="{cy + r_shell}" width="36" height="52" class="saddle" />')
        svg_lines.append(f'<text x="{sad_x}" y="{cy + r_shell + 32}" class="text-label" fill="#ffffff">{sad.get("tag", "Soporte")}</text>')
        
    # Componentes Principales
    for idx, comp in enumerate(seq):
        c_info = coords[comp]
        cx = c_info["start"]
        cw = c_info["width"]
        
        if idx > 0:
            svg_lines.append(f'<rect x="{cx - 10}" y="{cy - r_shell - 12}" width="10" height="{r_shell * 2 + 24}" class="flange" />')
            
        if comp == "BONNET":
            cap_depth = min(r_bonnet * 0.6, cw * 0.45)
            if idx == len(seq) - 1 or idx > 0:
                x_dome = cx + cw - cap_depth
                path = f"M {cx} {cy - r_bonnet} L {x_dome} {cy - r_bonnet} A {cap_depth} {r_bonnet} 0 0 1 {x_dome} {cy + r_bonnet} L {cx} {cy + r_bonnet} Z"
                label_x = cx + (x_dome - cx) / 2
            else:
                x_dome = cx + cap_depth
                path = f"M {cx + cw} {cy - r_bonnet} L {x_dome} {cy - r_bonnet} A {cap_depth} {r_bonnet} 0 0 0 {x_dome} {cy + r_bonnet} L {cx + cw} {cy + r_bonnet} Z"
                label_x = x_dome + (cx + cw - x_dome) / 2
                
            svg_lines.append(f'<path d="{path}" class="body" />')
            svg_lines.append(f'<text x="{label_x}" y="{cy + 5}" class="text-label">BONNET</text>')
        else:
            svg_lines.append(f'<rect x="{cx}" y="{cy - r_shell}" width="{cw}" height="{r_shell * 2}" class="body" />')
            svg_lines.append(f'<text x="{cx + cw / 2}" y="{cy + 5}" class="text-label">{comp}</text>')

    # Boquillas
    for noz in config.get("nozzles", []):
        comp = noz.get("component", "SHELL")
        c_info = coords.get(comp, coords.get("SHELL", {"start": 200, "width": 300}))
        ratio = float(noz.get("position_ratio", 0.5))
        nx = c_info["start"] + c_info["width"] * ratio
        side = noz.get("side", "TOP")
        tag = noz.get("tag", "N1")
        style = noz.get("style", "FLANGED")
        
        auxs = noz.get("auxiliaries", [])
        aux_txt = "/".join([a.get("position", "") for a in auxs if a.get("position")])
        
        active_r = r_bonnet if comp == "BONNET" else r_shell
        
        if side == "TOP":
            ny = cy - active_r
            if style == "FLANGED":
                svg_lines.append(f'<rect x="{nx - 10}" y="{ny - 40}" width="20" height="40" class="nozzle" />')
                svg_lines.append(f'<rect x="{nx - 16}" y="{ny - 48}" width="32" height="8" class="flange" />')
                svg_lines.append(f'<text x="{nx}" y="{ny - 54}" class="text-label">{tag}</text>')
                if aux_txt:
                    svg_lines.append(f'<text x="{nx}" y="{ny - 20}" class="sub-text">{aux_txt}</text>')
            else:
                svg_lines.append(f'<rect x="{nx - 6}" y="{ny - 25}" width="12" height="25" class="nozzle" />')
                svg_lines.append(f'<text x="{nx}" y="{ny - 30}" class="text-label">{tag}</text>')
        else: # BOTTOM
            ny = cy + active_r
            if style == "FLANGED":
                svg_lines.append(f'<rect x="{nx - 10}" y="{ny}" width="20" height="40" class="nozzle" />')
                svg_lines.append(f'<rect x="{nx - 16}" y="{ny + 40}" width="32" height="8" class="flange" />')
                svg_lines.append(f'<text x="{nx}" y="{ny + 62}" class="text-label">{tag}</text>')
                if aux_txt:
                    svg_lines.append(f'<text x="{nx}" y="{ny + 22}" class="sub-text">{aux_txt}</text>')
            else:
                svg_lines.append(f'<rect x="{nx - 6}" y="{ny}" width="12" height="25" class="nozzle" />')
                svg_lines.append(f'<text x="{nx}" y="{ny + 38}" class="text-label">{tag}</text>')

    svg_lines.append('</svg>')
    return "\n".join(svg_lines)

# -----------------------------------------------------------------------------
# BARRA LATERAL (SIDEBAR) - ETIQUETA "EQUIPO"
# -----------------------------------------------------------------------------
st.sidebar.title("🛠️ Editor de Diseño")

tag_inicial = st.session_state.get("tag_para_diseño", lista_equipos[0] if lista_equipos else "E-101")
idx_def = lista_equipos.index(tag_inicial) if tag_inicial in lista_equipos else 0

equipo_sel = st.sidebar.selectbox("EQUIPO", lista_equipos, index=idx_def)

if st.sidebar.button("⬅️ Volver a Vista Principal"):
    st.switch_page("Intercambiadores.py")

st.sidebar.markdown("---")

def cargar_config_inicial(tag):
    arch = f"config_{tag}.json"
    if os.path.exists(arch):
        try:
            with open(arch, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "equipment": {"tag": tag, "shell_diameter": 170, "bonnet_diameter": 170, "aux_rating": "6000#"},
        "components": {"channel_length": 150, "shell_length": 420, "bonnet_length": 100, "sequence": ["CHANNEL", "SHELL", "BONNET"]},
        "saddles": [
            {"id": "sad_1", "tag": "Soporte 1", "position_ratio": 0.30},
            {"id": "sad_2", "tag": "Soporte 2", "position_ratio": 0.70}
        ],
        "nozzles": [
            {"id": "noz_1", "tag": "S1", "service": "INLET", "component": "SHELL", "side": "TOP", "position_ratio": 0.10, "style": "FLANGED", "size": "8\"", "rating": "300#", "type": "RF WN", "auxiliaries": [{"position": "NS", "size": "3/4\""}, {"position": "FS", "size": "1\""}]},
            {"id": "noz_2", "tag": "S2", "service": "OUTLET", "component": "SHELL", "side": "BOTTOM", "position_ratio": 0.90, "style": "FLANGED", "size": "8\"", "rating": "300#", "type": "RF WN", "auxiliaries": [{"position": "NS", "size": "3/4\""}, {"position": "FS", "size": "1\""}]},
            {"id": "noz_3", "tag": "T1", "service": "INLET", "component": "CHANNEL", "side": "TOP", "position_ratio": 0.50, "style": "FLANGED", "size": "10\"", "rating": "300#", "type": "RF WN", "auxiliaries": [{"position": "NS", "size": "1\""}, {"position": "FS", "size": "1\""}]},
            {"id": "noz_4", "tag": "T2", "service": "OUTLET", "component": "CHANNEL", "side": "BOTTOM", "position_ratio": 0.50, "style": "FLANGED", "size": "10\"", "rating": "300#", "type": "RF WN", "auxiliaries": [{"position": "NS", "size": "1\""}, {"position": "FS", "size": "1\""}]}
        ]
    }

config = cargar_config_inicial(equipo_sel)

# -----------------------------------------------------------------------------
# PANEL CENTRAL Y FORMULARIO DE EDICIÓN
# -----------------------------------------------------------------------------
st.title(f"✏️ Configuración y Diseño Esquemático - {equipo_sel}")

col_izq, col_der = st.columns([1, 1.2])

with col_izq:
    st.subheader("⚙️ Parámetros del Equipo")
    aux_rating = st.text_input("Rating de Conexiones Auxiliares (CPLGS):", value=config.get("equipment", {}).get("aux_rating", "6000#"))
    
    st.markdown("##### 📏 Longitudes de Componentes")
    c_len = st.number_input("Channel Length (mm):", value=float(config["components"]["channel_length"]), step=10.0)
    s_len = st.number_input("Shell Length (mm):", value=float(config["components"]["shell_length"]), step=10.0)
    b_len = st.number_input("Bonnet Length (mm):", value=float(config["components"]["bonnet_length"]), step=10.0)
    
    config["equipment"]["aux_rating"] = aux_rating
    config["components"]["channel_length"] = c_len
    config["components"]["shell_length"] = s_len
    config["components"]["bonnet_length"] = b_len

    st.markdown("##### ⚓ Posición de Soportes (Saddles)")
    for i, sad in enumerate(config.get("saddles", [])):
        sad["position_ratio"] = st.slider(f"Posición {sad.get('tag', f'Soporte {i+1}')}:", 0.0, 1.0, float(sad.get("position_ratio", 0.5)), key=f"sad_pos_{i}")

with col_der:
    st.subheader("📌 Edición de Boquillas (Nozzles)")
    nozzles = config.get("nozzles", [])
    
    for idx, noz in enumerate(nozzles):
        with st.expander(f"Boquilla {noz.get('tag', 'N')} ({noz.get('component', 'SHELL')})", expanded=(idx==0)):
            noz["tag"] = st.text_input("TAG Boquilla:", value=noz.get("tag", ""), key=f"noz_tag_{idx}")
            noz["service"] = st.selectbox("Servicio:", ["INLET", "OUTLET", "DRAIN", "VENT", "PROCESS"], index=0 if noz.get("service")=="INLET" else 1, key=f"noz_serv_{idx}")
            noz["component"] = st.selectbox("Componente:", ["SHELL", "CHANNEL", "BONNET"], index=["SHELL", "CHANNEL", "BONNET"].index(noz.get("component", "SHELL")), key=f"noz_comp_{idx}")
            noz["side"] = st.radio("Orientación:", ["TOP", "BOTTOM"], index=0 if noz.get("side")=="TOP" else 1, horizontal=True, key=f"noz_side_{idx}")
            noz["position_ratio"] = st.slider("Posición relativa (0.0 - 1.0):", 0.0, 1.0, float(noz.get("position_ratio", 0.5)), key=f"noz_pos_{idx}")
            noz["size"] = st.text_input("Tamaño (ej: 8\"): ", value=noz.get("size", "8\""), key=f"noz_sz_{idx}")
            noz["rating"] = st.text_input("Rating (ej: 300#):", value=noz.get("rating", "300#"), key=f"noz_rt_{idx}")

# Renderizado en vivo del plano esquemático
st.markdown("---")
st.subheader("📐 Vista Previa del Plano Esquemático")
svg_code = generate_modular_exchanger_svg(config)

html_render = f"""
<div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; text-align: center;">
    {svg_code}
</div>
"""
components.html(html_render, height=480)

# -----------------------------------------------------------------------------
# BOTÓN DE GUARDADO AUTOMÁTICO A GOOGLE DRIVE / LOCAL
# -----------------------------------------------------------------------------
st.markdown("---")

col_g1, col_g2 = st.columns([2, 1])

with col_g1:
    if st.button("💾 GUARDAR CONFIGURACIÓN Y PLANO", type="primary", use_container_width=True):
        filename_json = f"config_{equipo_sel}.json"
        json_str = json.dumps(config, indent=2, ensure_ascii=False)
        
        # 1. Guardar en disco local
        with open(filename_json, "w", encoding="utf-8") as f:
            f.write(json_str)
            
        # 2. Guardar en memoria de sesión
        st.session_state[f"config_{equipo_sel}"] = config
        st.session_state["tag_para_diseño"] = equipo_sel
        
        # 3. Envío automático a Google Drive si la URL está configurada
        envio_cloud_ok = False
        if GOOGLE_SCRIPT_URL and "TU_URL_DE_DESPLIEGUE_AQUI" not in GOOGLE_SCRIPT_URL:
            try:
                payload = {
                    "tag": equipo_sel,
                    "folder_id": GDRIVE_FOLDER_ID,
                    "filename_json": filename_json,
                    "json_content": json_str,
                    "svg_content": svg_code
                }
                res = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=8)
                if res.status_code == 200:
                    envio_cloud_ok = True
            except Exception:
                envio_cloud_ok = False

        if envio_cloud_ok:
            st.success(f"✅ ¡Diseño guardado! La configuración y el plano de **{equipo_sel}** se subieron a tu carpeta de Google Drive.")
        else:
            st.success(f"✅ Configuración de **{equipo_sel}** guardada correctamente.")
            
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="📥 Descargar Archivo JSON de Respaldo",
                data=json_str,
                file_name=filename_json,
                mime="application/json",
                use_container_width=True
            )
        with col_d2:
            st.download_button(
                label="🖼️ Descargar Plano Vectorial SVG",
                data=svg_code,
                file_name=f"plano_{equipo_sel}.svg",
                mime="image/svg+xml",
                use_container_width=True
            )

with col_g2:
    st.link_button(
        label="📂 Abrir Carpeta Google Drive", 
        url=GDRIVE_FOLDER_URL, 
        use_container_width=True
    )
