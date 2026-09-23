import os
import re
import json
import urllib.parse
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from fpdf import FPDF

# Intentar importar la función generadora SVG de la página de diseño
generate_modular_exchanger_svg = None
for mod_path in ["pages.diseno", "pages.Diseño", "pages.diseño", "pages.Diseno"]:
    try:
        import importlib
        mod = importlib.import_module(mod_path)
        generate_modular_exchanger_svg = getattr(mod, "generate_modular_exchanger_svg", None)
        if generate_modular_exchanger_svg:
            break
    except Exception:
        continue

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="Gestión de Intercambiadores de Calor", layout="wide")

# ==========================================
# FUNCIONES AUXILIARES PARA PDF
# ==========================================
def sanitizar_para_pdf(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return texto.encode('latin-1', 'replace').decode('latin-1')

def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def obtener_config_equipo(val_equipo):
    val_clean = str(val_equipo).strip()
    posibles_archivos = [
        f"config_{val_clean}.json",
        f"config_{val_clean.upper()}.json",
        f"config_{val_clean.lower()}.json",
        f"config_{val_clean.replace('-', '')}.json",
        f"config_{val_clean.replace(' ', '')}.json"
    ]
    
    for arch in posibles_archivos:
        if os.path.exists(arch):
            try:
                with open(arch, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data:
                        return data
            except Exception:
                pass
                
    # Plantilla garantizada por defecto si no existe archivo previo
    return {
        "equipment": {"tag": val_clean, "shell_diameter": 170, "bonnet_diameter": 170, "aux_rating": "6000#"},
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

class PDFCustom(FPDF):
    def footer(self):
        pass

def dibujar_esquema_fpdf(pdf, config, x_offset=10, y_offset=120):
    cy = y_offset + 42
    seq = config.get("components", {}).get("sequence", ["CHANNEL", "SHELL", "BONNET"])
    
    comp_lens = {
        "CHANNEL": float(config.get("components", {}).get("channel_length", 150)),
        "SHELL": float(config.get("components", {}).get("shell_length", 420)),
        "BONNET": float(config.get("components", {}).get("bonnet_length", 100))
    }
    
    total_len = sum(comp_lens.get(c, 100) for c in seq)
    scale = 165.0 / max(total_len, 1.0)
    
    r_shell = 20.0
    r_bonnet = 20.0
    
    coords = {}
    curr_x = x_offset + 15
    
    for comp in seq:
        w_scaled = comp_lens.get(comp, 100) * scale
        coords[comp] = {"start": curr_x, "end": curr_x + w_scaled, "width": w_scaled}
        curr_x += w_scaled + 2
        
    pdf.set_draw_color(239, 68, 68)
    pdf.line(x_offset + 5, cy, curr_x + 8, cy)
    
    shell_info = coords.get("SHELL", {"start": x_offset + 50, "width": 80})
    for sad in config.get("saddles", []):
        sad_ratio = float(sad.get("position_ratio", 0.5))
        sad_x = shell_info["start"] + shell_info["width"] * sad_ratio
        pdf.set_fill_color(100, 116, 139)
        pdf.set_draw_color(15, 23, 42)
        pdf.rect(sad_x - 5, cy + r_shell, 10, 9, 'FD')
        
    for idx, comp in enumerate(seq):
        c_info = coords[comp]
        cx = c_info["start"]
        cw = c_info["width"]
        
        if idx > 0:
            pdf.set_fill_color(71, 85, 105)
            pdf.rect(cx - 2.5, cy - r_shell - 2.5, 2.5, r_shell * 2 + 5, 'FD')
            
        pdf.set_fill_color(226, 232, 240)
        pdf.set_draw_color(51, 65, 85)
        
        if comp == "BONNET":
            dome_w = min(15.0, cw * 0.4)
            if idx == len(seq) - 1:
                pdf.ellipse(cx + cw - 2*dome_w, cy - r_bonnet, 2*dome_w, 2*r_bonnet, style='FD')
                pdf.rect(cx, cy - r_bonnet, cw - dome_w + 0.5, 2*r_bonnet, style='F')
                pdf.line(cx, cy - r_bonnet, cx + cw - dome_w, cy - r_bonnet)
                pdf.line(cx, cy + r_bonnet, cx + cw - dome_w, cy + r_bonnet)
                pdf.line(cx, cy - r_bonnet, cx, cy + r_bonnet)
                label_x = cx + (cw - dome_w)/2 - 6
            else:
                pdf.ellipse(cx, cy - r_bonnet, 2*dome_w, 2*r_bonnet, style='FD')
                pdf.rect(cx + dome_w - 0.5, cy - r_bonnet, cw - dome_w + 0.5, 2*r_bonnet, style='F')
                pdf.line(cx + dome_w, cy - r_bonnet, cx + cw, cy - r_bonnet)
                pdf.line(cx + dome_w, cy + r_bonnet, cx + cw, cy + r_bonnet)
                pdf.line(cx + cw, cy - r_bonnet, cx + cw, cy + r_bonnet)
                label_x = cx + dome_w + (cw - dome_w)/2 - 6
        else:
            pdf.rect(cx, cy - r_shell, cw, r_shell * 2, 'FD')
            label_x = cx + cw / 2 - 6
        
        pdf.set_font("Arial", "B", 8)
        pdf.set_text_color(51, 65, 85)
        pdf.text(label_x, cy + 1.5, comp)

    for noz in config.get("nozzles", []):
        comp = noz.get("component", "SHELL")
        c_info = coords.get(comp, coords.get("SHELL"))
        ratio = float(noz.get("position_ratio", 0.5))
        nx = c_info["start"] + c_info["width"] * ratio
        
        style_type = noz.get("style", "FLANGED")
        side = noz.get("side", "TOP")
        tag_str = sanitizar_para_pdf(noz.get("tag", ""))
        
        auxs = noz.get("auxiliaries", [])
        active_r = r_bonnet if comp == "BONNET" else r_shell
        
        neck_h = 18.0
        neck_w = 9.0
        flange_w = 15.0
        flange_h = 3.5
        circ_r = 3.0
        
        if side == "TOP":
            ny = cy - active_r
            if style_type == "FLANGED":
                pdf.set_fill_color(203, 213, 225)
                pdf.set_draw_color(30, 41, 59)
                pdf.rect(nx - neck_w/2, ny - neck_h, neck_w, neck_h, 'FD')
                pdf.rect(nx - flange_w/2, ny - neck_h - flange_h, flange_w, flange_h, 'FD')
                pdf.set_font("Arial", "B", 8.5)
                pdf.set_text_color(15, 23, 42)
                pdf.text(nx - 3.5, ny - neck_h - flange_h - 2.5, tag_str)
                
                if len(auxs) == 2:
                    pdf.set_fill_color(255, 255, 255)
                    pdf.set_draw_color(15, 23, 42)
                    pdf.ellipse(nx - circ_r, ny - 13.5 - circ_r, circ_r*2, circ_r*2, 'FD')
                    pdf.set_font("Arial", "B", 6)
                    pdf.set_text_color(15, 23, 42)
                    pdf.text(nx - 2.2, ny - 13.5 + 1.1, sanitizar_para_pdf(auxs[0].get("position", "NS")))
                    
                    pdf.set_fill_color(255, 255, 255)
                    pdf.ellipse(nx - circ_r, ny - 5.5 - circ_r, circ_r*2, circ_r*2, 'FD')
                    pdf.set_font("Arial", "B", 6)
                    pdf.text(nx - 2.2, ny - 5.5 + 1.1, sanitizar_para_pdf(auxs[1].get("position", "FS")))
                elif len(auxs) == 1:
                    pdf.set_fill_color(255, 255, 255)
                    pdf.set_draw_color(15, 23, 42)
                    pdf.ellipse(nx - circ_r, ny - 9.5 - circ_r, circ_r*2, circ_r*2, 'FD')
                    pdf.set_font("Arial", "B", 6)
                    pdf.set_text_color(15, 23, 42)
                    pdf.text(nx - 2.2, ny - 9.5 + 1.1, sanitizar_para_pdf(auxs[0].get("position", "NS")))
            else:
                pdf.set_fill_color(148, 163, 184)
                pdf.set_draw_color(30, 41, 59)
                pdf.rect(nx - 2.5, ny - 9, 5, 9, 'FD')
                pdf.set_font("Arial", "B", 8)
                pdf.set_text_color(15, 23, 42)
                pdf.text(nx - 3.5, ny - 11, tag_str)
        else:
            ny = cy + active_r
            if style_type == "FLANGED":
                pdf.set_fill_color(203, 213, 225)
                pdf.set_draw_color(30, 41, 59)
                pdf.rect(nx - neck_w/2, ny, neck_w, neck_h, 'FD')
                pdf.rect(nx - flange_w/2, ny + neck_h, flange_w, flange_h, 'FD')
                pdf.set_font("Arial", "B", 8.5)
                pdf.set_text_color(15, 23, 42)
                pdf.text(nx - 3.5, ny + neck_h + flange_h + 5.5, tag_str)
                
                if len(auxs) == 2:
                    pdf.set_fill_color(255, 255, 255)
                    pdf.set_draw_color(15, 23, 42)
                    pdf.ellipse(nx - circ_r, ny + 5.5 - circ_r, circ_r*2, circ_r*2, 'FD')
                    pdf.set_font("Arial", "B", 6)
                    pdf.set_text_color(15, 23, 42)
                    pdf.text(nx - 2.2, ny + 5.5 + 1.1, sanitizar_para_pdf(auxs[0].get("position", "NS")))
                    
                    pdf.set_fill_color(255, 255, 255)
                    pdf.ellipse(nx - circ_r, ny + 13.5 - circ_r, circ_r*2, circ_r*2, 'FD')
                    pdf.set_font("Arial", "B", 6)
                    pdf.text(nx - 2.2, ny + 13.5 + 1.1, sanitizar_para_pdf(auxs[1].get("position", "FS")))
                elif len(auxs) == 1:
                    pdf.set_fill_color(255, 255, 255)
                    pdf.set_draw_color(15, 23, 42)
                    pdf.ellipse(nx - circ_r, ny + 9.5 - circ_r, circ_r*2, circ_r*2, 'FD')
                    pdf.set_font("Arial", "B", 6)
                    pdf.set_text_color(15, 23, 42)
                    pdf.text(nx - 2.2, ny + 9.5 + 1.1, sanitizar_para_pdf(auxs[0].get("position", "NS")))
            else:
                pdf.set_fill_color(148, 163, 184)
                pdf.set_draw_color(30, 41, 59)
                pdf.rect(nx - 2.5, ny, 5, 9, 'FD')
                pdf.set_font("Arial", "B", 8)
                pdf.set_text_color(15, 23, 42)
                pdf.text(nx - 3.5, ny + 14, tag_str)
                
    pdf.set_y(cy + r_shell + neck_h + flange_h + 12)

def agregar_tabla_nozzle_schedule_pdf(pdf, config_equipo, rgb_main):
    if pdf.get_y() + 45 > 270:
        pdf.add_page()
        
    pdf.ln(3)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(*rgb_main)
    tag_eq = sanitizar_para_pdf(config_equipo.get("equipment", {}).get("tag", ""))
    pdf.cell(0, 6, f"NOZZLE SCHEDULE - {tag_eq}", ln=True)
    pdf.ln(1)
    
    cols = [
        ("MK", 22),
        ("QT", 15),
        ("DESCRIPTION", 68),
        ("PROCESS", 30),
        ("AUXILLARIES", 45)
    ]
    
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.set_draw_color(51, 65, 85)
    
    for title, width in cols:
        pdf.cell(width, 5.5, f"  {title}", border=1, fill=True)
    pdf.ln()
    
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(0, 0, 0)
    
    nozzles = config_equipo.get("nozzles", [])
    global_aux_rating = config_equipo.get("equipment", {}).get("aux_rating", "6000#")
    
    for i, noz in enumerate(nozzles):
        if pdf.get_y() + 7 > 270:
            pdf.add_page()
            pdf.set_font("Arial", "B", 8)
            pdf.set_fill_color(30, 41, 59)
            pdf.set_text_color(255, 255, 255)
            for title, width in cols:
                pdf.cell(width, 5.5, f"  {title}", border=1, fill=True)
            pdf.ln()
            pdf.set_font("Arial", "", 8)
            pdf.set_text_color(0, 0, 0)
            
        mk = sanitizar_para_pdf(noz.get("tag", ""))
        qt = "1"
        
        size_desc = str(noz.get("size", "")).strip()
        rating_desc = str(noz.get("rating", "")).strip()
        type_desc = str(noz.get("type", "")).strip()
        rating_type = f"{rating_desc} {type_desc}".strip()
        desc_full = f"{size_desc} - {rating_type}" if size_desc and rating_type else (size_desc or rating_type)
        desc = sanitizar_para_pdf(desc_full)
        
        proc = sanitizar_para_pdf(noz.get("service", "INLET"))
        
        auxs = noz.get("auxiliaries", [])
        aux_parts = [f"{aux.get('size', '')} {aux.get('position', '')}" for aux in auxs]
        aux_txt = sanitizar_para_pdf("  ".join(aux_parts))
        
        fill_flag = (i % 2 == 1)
        if fill_flag:
            pdf.set_fill_color(248, 250, 252)
        else:
            pdf.set_fill_color(255, 255, 255)
            
        pdf.cell(22, 5, f"  {mk}", border=1, fill=fill_flag)
        pdf.cell(15, 5, f"  {qt}", border=1, fill=fill_flag)
        pdf.cell(68, 5, f"  {desc}", border=1, fill=fill_flag)
        pdf.cell(30, 5, f"  {proc}", border=1, fill=fill_flag)
        pdf.cell(45, 5, f"  {aux_txt}", border=1, fill=fill_flag)
        pdf.ln()
        
    if pdf.get_y() + 7 > 270:
        pdf.add_page()
    pdf.cell(22, 5, "", border=1)
    pdf.cell(15, 5, "", border=1)
    pdf.cell(68, 5, "", border=1)
    pdf.cell(30, 5, "", border=1)
    pdf.cell(45, 5, f"  {sanitizar_para_pdf(global_aux_rating)} CPLGS.", border=1)
    pdf.ln()

def generar_pdf_equipo(val_equipo, val_unidad, valor_status, datos_ficha, rgb_main, titulo_doc, config_equipo=None):
    pdf = PDFCustom()
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()
    
    if not config_equipo:
        config_equipo = obtener_config_equipo(val_equipo)
    
    # Encabezado
    pdf.set_fill_color(*rgb_main)
    pdf.rect(0, 0, 210, 20, 'F')
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(10, 6)
    pdf.cell(0, 8, sanitizar_para_pdf(titulo_doc), ln=True)
    
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.set_xy(10, 23)
    pdf.cell(0, 5, sanitizar_para_pdf(f"Unidad: {val_unidad} | Estado: {valor_status}"), ln=True)
    pdf.ln(4)
    
    # Tabla de Datos de Ficha Técnica
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(*rgb_main)
    pdf.cell(0, 6, "Datos Tecnicos del Equipo", ln=True)
    pdf.ln(1)
    
    pdf.set_font("Arial", "", 8)
    col_w = 92
    
    for idx, (param, valor) in enumerate(datos_ficha.items()):
        val_str = str(valor) if pd.notna(valor) and str(valor).strip() not in ["nan", "NAN", ""] else "-"
        p_clean = sanitizar_para_pdf(param)
        v_clean = sanitizar_para_pdf(val_str)
        
        pdf.set_fill_color(241, 245, 249) if idx % 4 in [0, 1] else pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(203, 213, 225)
        
        pdf.set_font("Arial", "B", 8)
        pdf.cell(42, 5, f" {p_clean}", border=1, fill=True)
        pdf.set_font("Arial", "", 8)
        pdf.cell(col_w - 42, 5, f" {v_clean}", border=1, fill=True)
        
        if idx % 2 == 1 or idx == len(datos_ficha) - 1:
            pdf.ln()
            
    # DIBUJAR PLANO ESQUEMÁTICO Y NOZZLE SCHEDULE EN EL PDF
    if pdf.get_y() + 90 > 270:
        pdf.add_page()
        
    pdf.ln(4)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(*rgb_main)
    pdf.cell(0, 6, "Plano Esquematico de Boquillas", ln=True)
    pdf.ln(2)
    
    y_esquema = pdf.get_y()
    dibujado_ok = False
    
    if generate_modular_exchanger_svg:
        try:
            import cairosvg
            svg_code = generate_modular_exchanger_svg(config_equipo)
            png_temp = f"temp_pdf_{sanitizar_para_pdf(val_equipo)}.png"
            cairosvg.svg2png(bytestring=svg_code.encode('utf-8'), write_to=png_temp, scale=2.0)
            pdf.image(png_temp, x=12, y=y_esquema, w=185)
            pdf.set_y(y_esquema + 92)
            if os.path.exists(png_temp):
                os.remove(png_temp)
            dibujado_ok = True
        except Exception:
            dibujado_ok = False
            
    if not dibujado_ok:
        dibujar_esquema_fpdf(pdf, config_equipo, x_offset=10, y_offset=y_esquema)
        
    agregar_tabla_nozzle_schedule_pdf(pdf, config_equipo, rgb_main)
    
    # SALIDA SEGURA EN BYTES (Inmune a TypeError en Python 3)
    try:
        out = pdf.output(dest='S')
        if isinstance(out, str):
            return out.encode('latin-1')
        return bytes(out)
    except Exception:
        out = pdf.output()
        if isinstance(out, str):
            return out.encode('latin-1')
        return bytes(out)

# ==========================================
# LECTURA DE GOOGLE SHEETS
# ==========================================
@st.cache_data(ttl=600)
def cargar_datos_sheets():
    sheet_id = "1lhpb211bqPyDAxxnBFgKaN7nY-WImR961xJ3mrIGYZ4"
    nombre_hoja = "Hoja 1"
    nombre_hoja_encoded = urllib.parse.quote(nombre_hoja)
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={nombre_hoja_encoded}"
    
    try:
        df = pd.read_csv(sheet_url)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()

df_raw = cargar_datos_sheets()

if df_raw.empty:
    st.warning("No se pudieron cargar los datos de la hoja de cálculo.")
    st.stop()

# ==========================================
# BÚSQUEDA Y SELECCIÓN DE EQUIPO
# ==========================================
col_eq_name = next((c for c in df_raw.columns if 'EQUIPO' in c.upper()), df_raw.columns[0])
lista_equipos = sorted([
    str(x).strip() for x in df_raw[col_eq_name].dropna().unique() 
    if str(x).strip() not in ["Sin información", "nan", "NAN", ""]
])

st.title("🔥 Gestión y Ficha Técnica de Intercambiadores")

equipo_seleccionado = st.selectbox("Seleccione el Equipo / Intercambiador:", options=lista_equipos)

df_equipo = df_raw[df_raw[col_eq_name].astype(str).str.strip() == equipo_seleccionado]

if df_equipo.empty:
    st.info("Seleccione un equipo válido para ver sus detalles.")
    st.stop()

fila_equipo = df_equipo.iloc[0]

# ==========================================
# OBTENER CONFIGURACIÓN DEL EQUIPO
# ==========================================
val_equipo_clean = str(equipo_seleccionado).strip()
config_equipo = obtener_config_equipo(val_equipo_clean)

# ==========================================
# MOSTRAR FICHA EN PANTALLA
# ==========================================
val_equipo = str(fila_equipo.get(col_eq_name, equipo_seleccionado))
col_unid_name = next((c for c in df_raw.columns if 'UNIDAD' in c.upper()), None)
val_unidad = str(fila_equipo.get(col_unid_name, "N/A")) if col_unid_name else "N/A"

col_stat_name = next((c for c in df_raw.columns if 'ESTADO' in c.upper() or 'STATUS' in c.upper()), None)
valor_status = str(fila_equipo.get(col_stat_name, "OPERATIVO")) if col_stat_name else "OPERATIVO"

color_principal = "#005CE6"
rgb_color = hex_to_rgb(color_principal)

col_detalles, col_enlaces = st.columns([2.3, 1])

with col_detalles:
    st.subheader(f"📄 Ficha Técnica: {val_equipo} ({val_unidad})")
    
    datos_ficha_reducida = {}
    for col in df_raw.columns:
        if col.upper() not in [col_eq_name.upper()]:
            val = fila_equipo.get(col, "-")
            datos_ficha_reducida[col] = str(val) if pd.notna(val) else "-"
            
    df_ficha_disp = pd.DataFrame(list(datos_ficha_reducida.items()), columns=["Parámetro", "Valor"])
    st.dataframe(df_ficha_disp, use_container_width=True, hide_index=True)

    # DIBUJAR PLANO ESQUEMÁTICO EN PANTALLA
    st.markdown("---")
    st.subheader(f"📐 Plano Esquemático de Boquillas - {val_equipo}")
    
    if generate_modular_exchanger_svg:
        svg_code = generate_modular_exchanger_svg(config_equipo)
        components.html(
            f'<div style="background:#ffffff; border:1px solid #cbd5e1; border-radius:8px; padding:10px; width:100%; height:100%; box-sizing:border-box; display:flex; justify-content:center; align-items:center;">{svg_code}</div>',
            height=500
        )
        
    # MOSTRAR TABLA NOZZLE SCHEDULE EN PANTALLA
    st.markdown(f"### 📋 NOZZLE SCHEDULE - {val_equipo}")
    table_rows = []
    global_aux_rating = config_equipo.get("equipment", {}).get("aux_rating", "6000#")

    for noz in config_equipo.get("nozzles", []):
        auxs = noz.get("auxiliaries", [])
        aux_parts = [f"{aux.get('size', '')} {aux.get('position', '')}" for aux in auxs]
        aux_combined = "  ".join(aux_parts) if aux_parts else ""

        size_desc = str(noz.get("size", "")).strip()
        rating_desc = str(noz.get("rating", "")).strip()
        type_desc = str(noz.get("type", "")).strip()
        
        rating_type = f"{rating_desc} {type_desc}".strip()
        desc_full = f"{size_desc} - {rating_type}" if size_desc and rating_type else (size_desc or rating_type)

        table_rows.append({
            "MK": noz["tag"],
            "QT": 1,
            "DESCRIPTION": desc_full,
            "PROCESS": noz.get("service", "INLET"),
            "AUXILLARIES": aux_combined
        })

    table_rows.append({
        "MK": "", "QT": "", "DESCRIPTION": "", "PROCESS": "", "AUXILLARIES": f"{global_aux_rating} CPLGS."
    })

    df_nozzles = pd.DataFrame(table_rows)

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

with col_enlaces:
    st.subheader("🚀 Acciones del Equipo")
    
    if st.button("✏️ Diseñar / Editar Esquema Paramétrico", use_container_width=True, type="primary"):
        st.session_state["tag_para_diseño"] = val_equipo
        for pag_diseño in ["pages/diseno.py", "pages/Diseño.py", "diseno.py"]:
            try:
                st.switch_page(pag_diseño)
                break
            except Exception:
                continue

    st.markdown("---")
    st.write("**Exportación:**")
    
    titulo_doc = f"Intercambiador {val_equipo} ({val_unidad})"
    pdf_bytes = generar_pdf_equipo(
        val_equipo, val_unidad, valor_status, datos_ficha_reducida, rgb_color, titulo_doc, config_equipo=config_equipo
    )
    
    st.download_button(
        label="📥 Descargar Ficha PDF para Terreno",
        data=pdf_bytes,
        file_name=f"Ficha_Tecnica_{val_equipo}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
