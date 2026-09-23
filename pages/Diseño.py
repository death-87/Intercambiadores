import os
import json
import requests
import urllib.parse
import pandas as pd
import streamlit as st
import xml.etree.ElementTree as ET
import streamlit.components.v1 as components

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="Diseño Paramétrico de Intercambiadores", layout="wide")

# ==========================================
# CONFIGURACIÓN DE GOOGLE DRIVE Y APPS SCRIPT
# ==========================================
GDRIVE_FOLDER_ID = "10hv3MlaXaL4rZkQrssnROAX18ms_31rc"
# PEGA AQUÍ TU URL COPIADA AL IMPLEMENTAR EN GOOGLE APPS SCRIPT (la que termina en /exec)
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/TU_URL_DE_DESPLIEGUE_AQUI/exec"

# ==========================================
# OBTENER LISTA REAL DE EQUIPOS DESDE GOOGLE SHEETS
# ==========================================
@st.cache_data(ttl=600)
def obtener_lista_equipos_oficiales():
    try:
        sheet_id = "1lhpb211bqPyDAxxnBFgKaN7nY-WImR961xJ3mrIGYZ4"
        nombre_hoja = "Hoja 1"
        nombre_hoja_encoded = urllib.parse.quote(nombre_hoja)
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={nombre_hoja_encoded}"
        
        data = pd.read_csv(sheet_url)
        col_eq = next((c for c in data.columns if 'EQUIPO' in c.upper()), None)
        if col_eq:
            lista = sorted([
                str(x).strip() for x in data[col_eq].dropna().unique() 
                if str(x).strip() not in ["Sin información", "nan", "NAN", ""]
            ])
            return lista
    except Exception:
        pass
    return []


# ==========================================
# 1. MOTOR SVG PARAMÉTRICO DE COMPONENTES
# ==========================================
def generate_modular_exchanger_svg(config, selected_id=None):
    width, height = 1000, 470
    svg = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg",
        "viewBox": f"0 0 {width} {height}",
        "preserveAspectRatio": "xMidYMid meet",
        "style": "width: 100%; height: 100%; max-width: 100%; max-height: 100%; display: block;",
        "id": "exchanger-svg"
    })

    defs = ET.SubElement(svg, "defs")
    
    style = ET.SubElement(defs, "style")
    style.text = """
        .component-body { fill: url(#metal-gradient); stroke: #334155; stroke-width: 2.2; }
        .flange-joint { fill: url(#metal-dark-gradient); stroke: #1e293b; stroke-width: 1.5; }
        .saddle-body { fill: #64748b; stroke: #0f172a; stroke-width: 2; transition: all 0.2s; }
        .centerline { stroke: #ef4444; stroke-width: 1.2; stroke-dasharray: 8,4,2,4; }
        
        .nozzle-neck { fill: url(#metal-gradient); stroke: #1e293b; stroke-width: 1.8; }
        .nozzle-flange { fill: url(#metal-dark-gradient); stroke: #0f172a; stroke-width: 2; }
        
        .plug-body { fill: url(#metal-gradient); stroke: #1e293b; stroke-width: 1.8; }
        .plug-line { stroke: #1e293b; stroke-width: 1.5; }

        .selected .nozzle-flange { fill: #0ea5e9 !important; stroke: #0369a1 !important; }
        .selected .nozzle-neck { fill: #38bdf8 !important; stroke: #0369a1 !important; }
        .selected .plug-body { fill: #38bdf8 !important; stroke: #0369a1 !important; }
        .selected .saddle-body { fill: #38bdf8 !important; stroke: #0284c7 !important; }
        .selected-box { fill: none; stroke: #0ea5e9; stroke-width: 2; stroke-dasharray: 4,3; }

        .nozzle-text { font-family: monospace; font-size: 13px; font-weight: bold; fill: #0f172a; text-anchor: middle; }
        .comp-label { font-family: sans-serif; font-size: 11px; font-weight: 700; fill: #334155; text-anchor: middle; }
        
        .marker-aux { fill: #ffffff; stroke: #0f172a; stroke-width: 1.2; }
        .text-aux { font-family: sans-serif; font-size: 8px; font-weight: bold; fill: #0f172a; text-anchor: middle; dominant-baseline: central; }
    """

    metal_grad = ET.SubElement(defs, "linearGradient", {"id": "metal-gradient", "x1": "0%", "y1": "0%", "x2": "0%", "y2": "100%"})
    ET.SubElement(metal_grad, "stop", {"offset": "0%", "stop-color": "#f1f5f9"})
    ET.SubElement(metal_grad, "stop", {"offset": "30%", "stop-color": "#cbd5e1"})
    ET.SubElement(metal_grad, "stop", {"offset": "70%", "stop-color": "#94a3b8"})
    ET.SubElement(metal_grad, "stop", {"offset": "100%", "stop-color": "#64748b"})

    metal_dark = ET.SubElement(defs, "linearGradient", {"id": "metal-dark-gradient", "x1": "0%", "y1": "0%", "x2": "0%", "y2": "100%"})
    ET.SubElement(metal_dark, "stop", {"offset": "0%", "stop-color": "#94a3b8"})
    ET.SubElement(metal_dark, "stop", {"offset": "50%", "stop-color": "#475569"})
    ET.SubElement(metal_dark, "stop", {"offset": "100%", "stop-color": "#334155"})

    cy = 225
    r_shell = config["equipment"]["shell_diameter"] / 2
    r_bonnet = config["equipment"].get("bonnet_diameter", config["equipment"]["shell_diameter"]) / 2
    
    w_channel = config["components"]["channel_length"]
    w_shell = config["components"]["shell_length"]
    w_bonnet = config["components"]["bonnet_length"]
    
    seq = config["components"].get("sequence", ["CHANNEL", "SHELL", "BONNET"])

    x_current = 140
    coords = {}
    
    widths = {
        "CHANNEL": w_channel,
        "SHELL": w_shell,
        "BONNET": w_bonnet
    }

    for comp in seq:
        coords[comp] = {
            "start": x_current,
            "end": x_current + widths[comp]
        }
        x_current = coords[comp]["end"] + 12

    main_layer = ET.SubElement(svg, "g", {"id": "assembly-layer"})

    ET.SubElement(main_layer, "line", {
        "x1": "40", "y1": str(cy), "x2": str(x_current + 30), "y2": str(cy), "class": "centerline"
    })

    saddles_layer = ET.SubElement(main_layer, "g", {"id": "saddles-layer"})
    saddle_y = cy + r_shell
    saddle_w, saddle_h = 28, 45

    shell_info = coords.get("SHELL", {"start": 140, "end": 140 + w_shell})
    for sad in config.get("saddles", []):
        sad_ratio = float(sad.get("position_ratio", 0.5))
        sad_x = shell_info["start"] + w_shell * sad_ratio
        is_sad_selected = (sad["id"] == selected_id)
        sad_class = "saddle-body selected" if is_sad_selected else "saddle-body"
        
        sad_g = ET.SubElement(saddles_layer, "g", {"id": sad["id"], "class": sad_class})
        ET.SubElement(sad_g, "path", {
            "d": f"M {sad_x - saddle_w/2} {saddle_y} L {sad_x - saddle_w/2 - 10} {saddle_y + saddle_h} L {sad_x + saddle_w/2 + 10} {saddle_y + saddle_h} L {sad_x + saddle_w/2} {saddle_y} Z",
            "class": "saddle-body"
        })

    for idx, comp in enumerate(seq):
        c_start = coords[comp]["start"]
        c_end = coords[comp]["end"]
        c_width = widths[comp]

        if idx > 0:
            ET.SubElement(main_layer, "rect", {"x": str(c_start - 10), "y": str(cy - r_shell - 8), "width": "10", "height": str(r_shell*2 + 16), "class": "flange-joint"})

        if comp == "SHELL":
            ET.SubElement(main_layer, "rect", {"x": str(c_start), "y": str(cy - r_shell), "width": str(c_width), "height": str(r_shell*2), "class": "component-body"})
            ET.SubElement(main_layer, "text", {"x": str(c_start + c_width/2), "y": str(cy + 4), "class": "comp-label"}).text = "SHELL"

        elif comp == "CHANNEL":
            ET.SubElement(main_layer, "rect", {"x": str(c_start), "y": str(cy - r_shell), "width": str(c_width), "height": str(r_shell*2), "class": "component-body"})
            ET.SubElement(main_layer, "text", {"x": str(c_start + c_width/2), "y": str(cy + 4), "class": "comp-label"}).text = "CHANNEL"

        elif comp == "BONNET":
            if idx == 0:
                bonnet_path = f"M {c_end} {cy - r_bonnet} L {c_end - 20} {cy - r_bonnet} A {r_bonnet} {r_bonnet} 0 0 0 {c_end - 20} {cy + r_bonnet} L {c_end} {cy + r_bonnet} Z"
                label_x = c_end - 30
            else:
                bonnet_path = f"M {c_start} {cy - r_bonnet} L {c_start + 20} {cy - r_bonnet} A {r_bonnet} {r_bonnet} 0 0 1 {c_start + 20} {cy + r_bonnet} L {c_start} {cy + r_bonnet} Z"
                label_x = c_start + 30

            ET.SubElement(main_layer, "path", {"d": bonnet_path, "class": "component-body"})
            ET.SubElement(main_layer, "text", {"x": str(label_x), "y": str(cy + 4), "class": "comp-label"}).text = "BONNET"

        if idx < len(seq) - 1:
            ET.SubElement(main_layer, "rect", {"x": str(c_end), "y": str(cy - r_shell - 8), "width": "12", "height": str(r_shell*2 + 16), "class": "flange-joint"})

    nozzles_layer = ET.SubElement(svg, "g", {"id": "nozzles-layer"})

    for noz in config["nozzles"]:
        is_selected = (noz["id"] == selected_id)
        group_class = "nozzle-group selected" if is_selected else "nozzle-group"
        noz_g = ET.SubElement(nozzles_layer, "g", {"id": noz["id"], "class": group_class})

        comp = noz.get("component", "SHELL")
        ratio = float(noz.get("position_ratio", 0.5))
        style_type = noz.get("style", "FLANGED")

        comp_data = coords.get(comp, coords["SHELL"])
        nx = comp_data["start"] + widths[comp] * ratio

        label_str = noz["tag"]
        auxiliaries = noz.get("auxiliaries", [])
        
        neck_width = 24
        neck_height = 52
        flange_width = 44

        active_r = r_bonnet if comp == "BONNET" else r_shell

        if noz.get("side", "TOP") == "TOP":
            ny_base = cy - active_r

            if style_type == "FLANGED":
                ny_flange = ny_base - neck_height
                if is_selected:
                    ET.SubElement(noz_g, "rect", {"x": str(nx - 28), "y": str(ny_flange - 8), "width": "56", "height": str(neck_height + 16), "class": "selected-box", "rx": "4"})

                ET.SubElement(noz_g, "rect", {"x": str(nx - neck_width/2), "y": str(ny_flange), "width": str(neck_width), "height": str(neck_height), "class": "nozzle-neck"})
                ET.SubElement(noz_g, "rect", {"x": str(nx - flange_width/2), "y": str(ny_flange), "width": str(flange_width), "height": "9", "class": "nozzle-flange"})
                ET.SubElement(noz_g, "text", {"x": str(nx), "y": str(ny_flange - 12), "class": "nozzle-text"}).text = label_str
                
                if len(auxiliaries) == 2:
                    y_first = ny_flange + 34
                    y_second = ny_flange + 18
                    ET.SubElement(noz_g, "circle", {"cx": str(nx), "cy": str(y_first), "r": "7", "class": "marker-aux"})
                    ET.SubElement(noz_g, "text", {"x": str(nx), "y": str(y_first), "class": "text-aux"}).text = auxiliaries[0]["position"]
                    ET.SubElement(noz_g, "circle", {"cx": str(nx), "cy": str(y_second), "r": "7", "class": "marker-aux"})
                    ET.SubElement(noz_g, "text", {"x": str(nx), "y": str(y_second), "class": "text-aux"}).text = auxiliaries[1]["position"]
                elif len(auxiliaries) == 1:
                    y_single = ny_flange + 26
                    ET.SubElement(noz_g, "circle", {"cx": str(nx), "cy": str(y_single), "r": "8", "class": "marker-aux"})
                    ET.SubElement(noz_g, "text", {"x": str(nx), "y": str(y_single), "class": "text-aux"}).text = auxiliaries[0]["position"]
            else:
                ny_plug = ny_base - 14
                if is_selected:
                    ET.SubElement(noz_g, "rect", {"x": str(nx - 14), "y": str(ny_plug - 6), "width": "28", "height": "32", "class": "selected-box", "rx": "3"})

                ET.SubElement(noz_g, "rect", {"x": str(nx - 6), "y": str(ny_plug), "width": "12", "height": "14", "class": "plug-body"})
                ET.SubElement(noz_g, "line", {"x1": str(nx), "y1": str(ny_plug - 4), "x2": str(nx), "y2": str(ny_base + 20), "class": "plug-line"})
                ET.SubElement(noz_g, "text", {"x": str(nx), "y": str(ny_plug - 10), "class": "nozzle-text"}).text = label_str

        elif noz.get("side") == "BOTTOM":
            ny_base = cy + active_r

            if style_type == "FLANGED":
                ny_flange = ny_base + neck_height
                if is_selected:
                    ET.SubElement(noz_g, "rect", {"x": str(nx - 28), "y": str(ny_base - 6), "width": "56", "height": str(neck_height + 16), "class": "selected-box", "rx": "4"})

                ET.SubElement(noz_g, "rect", {"x": str(nx - neck_width/2), "y": str(ny_base), "width": str(neck_width), "height": str(neck_height), "class": "nozzle-neck"})
                ET.SubElement(noz_g, "rect", {"x": str(nx - flange_width/2), "y": str(ny_flange - 9), "width": str(flange_width), "height": "9", "class": "nozzle-flange"})
                ET.SubElement(noz_g, "text", {"x": str(nx), "y": str(ny_flange + 20), "class": "nozzle-text"}).text = label_str
                
                if len(auxiliaries) == 2:
                    y_first = ny_base + 18
                    y_second = ny_base + 34
                    ET.SubElement(noz_g, "circle", {"cx": str(nx), "cy": str(y_first), "r": "7", "class": "marker-aux"})
                    ET.SubElement(noz_g, "text", {"x": str(nx), "y": str(y_first), "class": "text-aux"}).text = auxiliaries[0]["position"]
                    ET.SubElement(noz_g, "circle", {"cx": str(nx), "cy": str(y_second), "r": "7", "class": "marker-aux"})
                    ET.SubElement(noz_g, "text", {"x": str(nx), "y": str(y_second), "class": "text-aux"}).text = auxiliaries[1]["position"]
                elif len(auxiliaries) == 1:
                    y_single = ny_base + 26
                    ET.SubElement(noz_g, "circle", {"cx": str(nx), "cy": str(y_single), "r": "8", "class": "marker-aux"})
                    ET.SubElement(noz_g, "text", {"x": str(nx), "y": str(y_single), "class": "text-aux"}).text = auxiliaries[0]["position"]
            else:
                ny_plug = ny_base + 14
                if is_selected:
                    ET.SubElement(noz_g, "rect", {"x": str(nx - 14), "y": str(ny_base - 6), "width": "28", "height": "32", "class": "selected-box", "rx": "3"})

                ET.SubElement(noz_g, "rect", {"x": str(nx - 6), "y": str(ny_base), "width": "12", "height": "14", "class": "plug-body"})
                ET.SubElement(noz_g, "line", {"x1": str(nx), "y1": str(ny_base - 20), "x2": str(nx), "y2": str(ny_plug + 4), "class": "plug-line"})
                ET.SubElement(noz_g, "text", {"x": str(nx), "y": str(ny_plug + 20), "class": "nozzle-text"}).text = label_str

    return ET.tostring(svg, encoding="unicode")


# ==========================================
# 2. ESTADOS INICIALES EN SESSION_STATE
# ==========================================
if "exchanger_data" not in st.session_state:
    st.session_state.exchanger_data = {
        "equipment": {"tag": "C702", "shell_diameter": 170, "bonnet_diameter": 170, "aux_rating": "6000#"},
        "components": {
            "channel_length": 150,
            "shell_length": 420,
            "bonnet_length": 100,
            "sequence": ["CHANNEL", "SHELL", "BONNET"]
        },
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

if "aux_rating" not in st.session_state.exchanger_data["equipment"]:
    st.session_state.exchanger_data["equipment"]["aux_rating"] = "6000#"

if "bonnet_diameter" not in st.session_state.exchanger_data["equipment"]:
    st.session_state.exchanger_data["equipment"]["bonnet_diameter"] = st.session_state.exchanger_data["equipment"]["shell_diameter"]

if "sequence" not in st.session_state.exchanger_data["components"]:
    st.session_state.exchanger_data["components"]["sequence"] = ["CHANNEL", "SHELL", "BONNET"]

# Carga automática si venimos redirigidos desde la página principal
if "tag_para_diseño" in st.session_state:
    tag_recibido = st.session_state.pop("tag_para_diseño")
    st.session_state.exchanger_data["equipment"]["tag"] = tag_recibido
    archivo_auto = f"config_{tag_recibido}.json"
    if os.path.exists(archivo_auto):
        try:
            with open(archivo_auto, "r", encoding="utf-8") as f:
                st.session_state.exchanger_data = json.load(f)
        except Exception:
            pass

# ==========================================
# 3. INTERFAZ Y BARRA LATERAL
# ==========================================
st.sidebar.markdown("### 🏷️ Equipo Seleccionado (Tabla Google Sheets)")

lista_equipos_oficiales = obtener_lista_equipos_oficiales()
tag_actual = st.session_state.exchanger_data["equipment"].get("tag", "C702")

if lista_equipos_oficiales:
    idx_default = lista_equipos_oficiales.index(tag_actual) if tag_actual in lista_equipos_oficiales else 0
    selected_tag_from_list = st.sidebar.selectbox(
        "Seleccionar TAG oficial (Columna 'Equipo'):", 
        options=lista_equipos_oficiales, 
        index=idx_default,
        key="select_official_tag"
    )
    
    if selected_tag_from_list != st.session_state.exchanger_data["equipment"].get("tag"):
        st.session_state.exchanger_data["equipment"]["tag"] = selected_tag_from_list
        archivo_sel = f"config_{selected_tag_from_list}.json"
        if os.path.exists(archivo_sel):
            try:
                with open(archivo_sel, "r", encoding="utf-8") as f:
                    st.session_state.exchanger_data = json.load(f)
            except Exception:
                pass
        st.rerun()
    tag_actual = selected_tag_from_list
else:
    tag_actual = st.sidebar.text_input("TAG del Intercambiador:", value=tag_actual)
    st.session_state.exchanger_data["equipment"]["tag"] = tag_actual

archivo_json = f"config_{tag_actual}.json"

col_save1, col_save2 = st.sidebar.columns(2)
with col_save1:
    if st.button("💾 Guardar", type="primary", use_container_width=True):
        st.session_state.exchanger_data["equipment"]["tag"] = tag_actual
        
        # 1. Guardado local en disco
        json_str = json.dumps(st.session_state.exchanger_data, indent=4, ensure_ascii=False)
        with open(archivo_json, "w", encoding="utf-8") as f:
            f.write(json_str)
            
        # 2. Envío a Google Drive vía Webhook si la URL está lista
        envio_cloud_ok = False
        if GOOGLE_SCRIPT_URL and "TU_URL_DE_DESPLIEGUE_AQUI" not in GOOGLE_SCRIPT_URL:
            try:
                svg_code_save = generate_modular_exchanger_svg(st.session_state.exchanger_data)
                payload = {
                    "tag": tag_actual,
                    "folder_id": GDRIVE_FOLDER_ID,
                    "filename_json": archivo_json,
                    "json_content": json_str,
                    "svg_content": svg_code_save
                }
                res = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=8)
                if res.status_code == 200:
                    envio_cloud_ok = True
            except Exception:
                envio_cloud_ok = False

        if envio_cloud_ok:
            st.sidebar.success(f"¡Guardado local y en Google Drive para {tag_actual}!")
        else:
            st.sidebar.success(f"¡Guardado local para {tag_actual}!")

with col_save2:
    if os.path.exists(archivo_json):
        if st.button("📂 Cargar", use_container_width=True):
            with open(archivo_json, "r", encoding="utf-8") as f:
                st.session_state.exchanger_data = json.load(f)
            st.sidebar.success(f"¡Cargado desde {archivo_json}!")
            st.rerun()

# Retorno seguro a la página principal
if st.sidebar.button("🏠 Volver a Página Principal", use_container_width=True):
    for root_page in ["Intercambiadores.py", "intercambiadores.py"]:
        try:
            st.switch_page(root_page)
            break
        except Exception:
            continue

st.sidebar.divider()

with st.sidebar.expander("📐 Secuencia y Dimensiones del Equipo"):
    with st.form("form_edit_components"):
        st.write("**Secuencia de Izquierda a Derecha:**")
        current_seq = st.session_state.exchanger_data["components"]["sequence"]
        
        seq_labels = [
            "Channel (Izq) -> Shell -> Bonnet (Der)",
            "Bonnet (Izq) -> Shell -> Channel (Der)"
        ]
        
        default_idx = 0 if current_seq == ["CHANNEL", "SHELL", "BONNET"] else 1
        chosen_seq_label = st.selectbox("Seleccione Secuencia:", seq_labels, index=default_idx)

        st.divider()
        new_ch_len = st.slider("Largo Channel", 100, 250, int(st.session_state.exchanger_data["components"]["channel_length"]))
        new_sh_len = st.slider("Largo Shell", 250, 650, int(st.session_state.exchanger_data["components"]["shell_length"]))
        new_bo_len = st.slider("Largo Bonnet", 60, 180, int(st.session_state.exchanger_data["components"]["bonnet_length"]))
        new_diam = st.slider("Diámetro de Shell / Channel", 120, 240, int(st.session_state.exchanger_data["equipment"]["shell_diameter"]))
        new_bonnet_diam = st.slider("Diámetro de Bonnet", 120, 260, int(st.session_state.exchanger_data["equipment"].get("bonnet_diameter", 170)))

        if st.form_submit_button("Aplicar Cambios"):
            new_sequence = ["CHANNEL", "SHELL", "BONNET"] if chosen_seq_label.startswith("Channel") else ["BONNET", "SHELL", "CHANNEL"]
            st.session_state.exchanger_data["components"]["sequence"] = new_sequence
            st.session_state.exchanger_data["components"]["channel_length"] = new_ch_len
            st.session_state.exchanger_data["components"]["shell_length"] = new_sh_len
            st.session_state.exchanger_data["components"]["bonnet_length"] = new_bo_len
            st.session_state.exchanger_data["equipment"]["shell_diameter"] = new_diam
            st.session_state.exchanger_data["equipment"]["bonnet_diameter"] = new_bonnet_diam
            st.rerun()

st.sidebar.divider()

with st.sidebar.expander("➕ Crear Nueva Boquilla"):
    new_srv = st.selectbox("Process", ["INLET", "OUTLET", "VENT", "DRAIN", "INSTRUMENT"], key="sidebar_new_srv")
    
    is_vent_drain = new_srv in ["VENT", "DRAIN"]
    
    prefix_map = {"VENT": "V", "DRAIN": "D", "INLET": "S", "OUTLET": "S", "INSTRUMENT": "PI"}
    default_prefix = prefix_map.get(new_srv, "S")
    count_srv = sum(1 for n in st.session_state.exchanger_data["nozzles"] if n.get("service") == new_srv) + 1
    
    new_tag = st.text_input("MK (Tag)", value=f"{default_prefix}{count_srv}", key="sidebar_new_tag")
    
    style_default = 1 if is_vent_drain else 0
    new_style = st.selectbox("Estilo", ["FLANGED", "TAPÓN / COUPLING"], index=style_default, key="sidebar_new_style")
    new_comp = st.selectbox("Componente", ["SHELL", "CHANNEL", "BONNET"], key="sidebar_new_comp")
    
    side_default = 0 if new_srv == "VENT" else (1 if new_srv == "DRAIN" else 0)
    new_side = st.selectbox("Lado", ["TOP", "BOTTOM"], index=side_default, key="sidebar_new_side")
    
    if is_vent_drain or new_style == "TAPÓN / COUPLING":
        new_size = st.selectbox("Tamaño", ["3/4\"", "1/2\"", "1\"", "1.1/2\"", "2\""], key="sidebar_new_size_sel")
        new_rating = st.selectbox("Rating", ["6000#CPLG", "3000#CPLG"], key="sidebar_new_rating_sel")
        new_type = st.text_input("Tipo / Tipo Brida", value="", key="sidebar_new_type_txt_cplg")
    else:
        new_size = st.text_input("Tamaño", value="8\"", key="sidebar_new_size_txt")
        new_rating = st.text_input("Rating", value="300#", key="sidebar_new_rating_txt")
        new_type = st.text_input("Tipo / Tipo Brida", value="RF WN", key="sidebar_new_type_txt_flg")
    
    if st.button("➕ Crear Boquilla", use_container_width=True, key="sidebar_btn_create"):
        default_ratio = 0.20 if is_vent_drain else 0.50
        st.session_state.exchanger_data["nozzles"].append({
            "id": f"noz_{len(st.session_state.exchanger_data['nozzles'])+1}",
            "tag": new_tag,
            "service": new_srv,
            "style": new_style,
            "component": new_comp,
            "side": new_side,
            "position_ratio": default_ratio,
            "size": new_size,
            "rating": new_rating,
            "type": new_type,
            "auxiliaries": []
        })
        st.rerun()

st.sidebar.divider()

nozzle_options = {f"📌 Boquilla: {noz['tag']} ({noz['component']})": noz['id'] for noz in st.session_state.exchanger_data["nozzles"]}
saddle_options = {f"🛋️ {sad['tag']}": sad['id'] for sad in st.session_state.exchanger_data["saddles"]}
all_options = {**nozzle_options, **saddle_options}

selected_label = st.sidebar.radio("🔍 Seleccionar Elemento para Editar:", options=list(all_options.keys()) if all_options else [])
selected_id = all_options.get(selected_label)

st.title(f"🛠️ Constructor Paramétrico: {st.session_state.exchanger_data['equipment']['tag']}")

col_view, col_control = st.columns([2.3, 1])

with col_view:
    st.subheader(f"Plano Esquemático SVG - Equipo: {st.session_state.exchanger_data['equipment']['tag']}")
    svg_code = generate_modular_exchanger_svg(st.session_state.exchanger_data, selected_id=selected_id)
    
    components.html(
        f'<div style="background:#ffffff; border:1px solid #cbd5e1; border-radius:8px; padding:10px; width:100%; height:100%; box-sizing:border-box; display:flex; justify-content:center; align-items:center;">{svg_code}</div>', 
        height=520
    )

    st.markdown(f"### 📋 NOZZLE SCHEDULE - {st.session_state.exchanger_data['equipment']['tag']}")
    
    table_rows = []
    global_aux_rating = st.session_state.exchanger_data["equipment"].get("aux_rating", "6000#")

    for noz in st.session_state.exchanger_data["nozzles"]:
        auxs = noz.get("auxiliaries", [])
        aux_parts = [f"{aux.get('size', '')} {aux.get('position', '')}" for aux in auxs]
        aux_combined = "  ".join(aux_parts) if aux_parts else ""

        size_desc = str(noz.get("size", "")).strip()
        rating_desc = str(noz.get("rating", "")).strip()
        type_desc = str(noz.get("type", "")).strip()
        
        rating_type = f"{rating_desc} {type_desc}".strip()
        if size_desc and rating_type:
            desc_full = f"{size_desc} - {rating_type}"
        else:
            desc_full = size_desc or rating_type

        table_rows.append({
            "MK": noz["tag"],
            "QT": 1,
            "DESCRIPTION": desc_full,
            "PROCESS": noz.get("service", "INLET"),
            "AUXILIARIES": aux_combined
        })

    table_rows.append({
        "MK": "", "QT": "", "DESCRIPTION": "", "PROCESS": "", "AUXILIARIES": f"{global_aux_rating} CPLGS."
    })

    df_nozzles = pd.DataFrame(table_rows)

    # ESTILOS CSS CON TAMAÑO UN 20% MÁS GRANDE (13.2px)
    st.markdown("""
        <style>
        [data-testid="stTable"] {
            width: fit-content !important;
            max-width: 100% !important;
            margin-top: 5px;
        }
        [data-testid="stTable"] table {
            width: auto !important;
        }
        [data-testid="stTable"] th {
            font-size: 13.2px !important;
            padding: 7px 14px !important;
            font-weight: 700 !important;
            white-space: nowrap !important;
            background-color: #1e293b !important;
            color: #ffffff !important;
            border: 1px solid #334155 !important;
        }
        [data-testid="stTable"] td {
            font-size: 13.2px !important;
            padding: 6px 14px !important;
            white-space: nowrap !important;
            line-height: 1.3 !important;
            border: 1px solid #334155 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.table(df_nozzles.style.hide(axis='index'))

    # FOTO FRANJA2.PNG ROBUSTA (DEBAJO DE LA TABLA NOZZLE SCHEDULE)
    st.markdown("<br>", unsafe_allow_html=True)
    
    rutas_franja = [
        "franja2.png",
        "franja2.PNG",
        "FRANJA2.PNG",
        "franja2.jpg",
        "franja2.jpeg",
        os.path.join(os.path.dirname(__file__), "franja2.png"),
        os.path.join(os.path.dirname(__file__), "..", "franja2.png"),
        os.path.join(os.path.dirname(__file__), "franja2.PNG"),
        os.path.join(os.path.dirname(__file__), "..", "franja2.PNG"),
        "franja.png",
        "franja.jpg"
    ]
    
    franja_dibujada = False
    for ruta in rutas_franja:
        if os.path.exists(ruta):
            st.image(ruta, use_container_width=True)
            franja_dibujada = True
            break
            
    if not franja_dibujada:
        try:
            st.image("franja2.png", use_container_width=True)
        except Exception:
            pass

with col_control:
    tab_noz, tab_aux, tab_saddles = st.tabs(["⚙️ Boq. / Tapón", "🔌 NS/FS (Editar)", "🛋️ Soportes"])

    selected_noz = next((n for n in st.session_state.exchanger_data["nozzles"] if n["id"] == selected_id), None)

    with tab_noz:
        if selected_noz:
            st.info(f"📍 Editando: **{selected_noz['tag']}**")
            with st.form("form_edit_noz"):
                tag_val = st.text_input("MK (Tag)", value=selected_noz["tag"])
                
                service_opts = ["INLET", "OUTLET", "VENT", "DRAIN", "INSTRUMENT"]
                curr_srv = selected_noz.get("service", "INLET")
                srv_idx = service_opts.index(curr_srv) if curr_srv in service_opts else 0
                service_val = st.selectbox("Process", service_opts, index=srv_idx)
                
                style_val = st.selectbox("Representación", ["FLANGED", "TAPÓN / COUPLING"], index=0 if selected_noz.get("style", "FLANGED") == "FLANGED" else 1)
                comp_val = st.selectbox("Componente:", ["CHANNEL", "SHELL", "BONNET"], index=["CHANNEL", "SHELL", "BONNET"].index(selected_noz.get("component", "SHELL")))
                
                size_val = st.text_input("Tamaño", value=selected_noz.get("size", ""))
                rating_val = st.text_input("Rating", value=selected_noz.get("rating", ""))
                type_val = st.text_input("Tipo (ej. RF WN)", value=selected_noz.get("type", ""))
                
                side_val = st.selectbox("Orientación", ["TOP", "BOTTOM"], index=0 if selected_noz.get("side")=="TOP" else 1)
                ratio_val = st.slider("Posición horizontal", 0.05, 0.95, float(selected_noz.get("position_ratio", 0.5)))

                if st.form_submit_button("💾 Guardar Cambios"):
                    selected_noz["tag"] = tag_val
                    selected_noz["service"] = service_val
                    selected_noz["style"] = style_val
                    selected_noz["component"] = comp_val
                    selected_noz["size"] = size_val
                    selected_noz["rating"] = rating_val
                    selected_noz["type"] = type_val
                    selected_noz["side"] = side_val
                    selected_noz["position_ratio"] = ratio_val
                    st.rerun()

            if st.button(f"🗑️ Eliminar {selected_noz['tag']}"):
                st.session_state.exchanger_data["nozzles"] = [n for n in st.session_state.exchanger_data["nozzles"] if n["id"] != selected_id]
                st.rerun()
        else:
            st.caption("Selecciona una boquilla en la barra lateral.")

    with tab_aux:
        st.write("**Rating Global de Auxiliares:**")
        current_global_rating = st.session_state.exchanger_data["equipment"].get("aux_rating", "6000#")
        new_global_rating = st.selectbox("Rating General para CPLGS:", ["3000#", "6000#"], index=["3000#", "6000#"].index(current_global_rating) if current_global_rating in ["3000#", "6000#"] else 1)
        if new_global_rating != current_global_rating:
            st.session_state.exchanger_data["equipment"]["aux_rating"] = new_global_rating
            st.rerun()

        st.divider()

        if selected_noz:
            st.write(f"Auxiliares en **{selected_noz['tag']}**:")
            for idx, aux in enumerate(selected_noz.get("auxiliaries", [])):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    new_pos_text = st.text_input(f"Etiqueta #{idx+1}", value=aux.get("position", ""), key=f"edit_pos_{selected_noz['id']}_{idx}")
                    new_sz_text = st.text_input(f"Medida #{idx+1}", value=aux.get("size", ""), key=f"edit_sz_{selected_noz['id']}_{idx}")
                    if new_pos_text != aux.get("position") or new_sz_text != aux.get("size"):
                        aux["position"] = new_pos_text
                        aux["size"] = new_sz_text
                with col_b:
                    if st.button("🗑️", key=f"del_aux_{selected_noz['id']}_{idx}"):
                        selected_noz["auxiliaries"].pop(idx)
                        st.rerun()

            st.divider()
            st.write("**Añadir Nuevo Auxiliar / Conexión:**")
            with st.form("form_add_aux"):
                aux_pos = st.text_input("Texto / Etiqueta", value="NS")
                aux_size = st.text_input("Medida", value="3/4\"")
                if st.form_submit_button("➕ Añadir"):
                    selected_noz["auxiliaries"].append({"position": aux_pos, "size": aux_size})
                    st.rerun()
        else:
            st.caption("Selecciona una boquilla para configurar sus auxiliares.")

    with tab_saddles:
        st.write("**Soportes de Apoyo:**")
        for idx, sad in enumerate(st.session_state.exchanger_data.get("saddles", [])):
            with st.expander(f"🛋️ {sad['tag']}", expanded=(sad["id"] == selected_id)):
                sad_tag = st.text_input("Nombre", value=sad["tag"], key=f"sad_tag_{sad['id']}")
                sad_ratio = st.slider("Posición en Shell", 0.05, 0.95, float(sad["position_ratio"]), step=0.01, key=f"sad_pos_{sad['id']}")
                
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    if st.button("💾", key=f"save_sad_{sad['id']}"):
                        sad["tag"] = sad_tag
                        sad["position_ratio"] = sad_ratio
                        st.rerun()
                with col_s2:
                    if st.button("🗑️", key=f"del_sad_{sad['id']}"):
                        st.session_state.exchanger_data.get("saddles", []).pop(idx)
                        st.rerun()

        st.divider()
        st.write("**Añadir Soporte:**")
        with st.form("form_add_saddle"):
            new_sad_tag = st.text_input("Nombre", value=f"Soporte {len(st.session_state.exchanger_data.get('saddles', []))+1}")
            new_sad_pos = st.slider("Posición inicial", 0.05, 0.95, 0.5)
            if st.form_submit_button("➕ Añadir"):
                new_sad_id = f"sad_{len(st.session_state.exchanger_data.get('saddles', []))+1}"
                st.session_state.exchanger_data.setdefault("saddles", []).append({
                    "id": new_sad_id, "tag": new_sad_tag, "position_ratio": new_sad_pos
                })
                st.rerun()
