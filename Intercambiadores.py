import os
import re
import json
import unicodedata
import urllib.parse
import pandas as pd
import streamlit as st
import plotly.express as px
import streamlit.components.v1 as components
from fpdf import FPDF

# -----------------------------------------------------------------------------
# NAVEGACIÓN SEGURA Y CARGA DE MÓDULOS (SOPORTE PARA MAYÚSCULAS/TILDES)
# -----------------------------------------------------------------------------
def ir_base_diseno():
    paginas_posibles = [
        "pages/diseno.py",
        "pages/Diseño.py",
        "pages/diseño.py",
        "pages/Diseno.py"
    ]
    for pag in paginas_posibles:
        try:
            st.switch_page(pag)
            return
        except Exception:
            continue
    st.error("❌ No se encontró el archivo de diseño en la carpeta 'pages/'. Revisa que esté subido como 'pages/diseno.py'.")

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

# Configuración de página de Streamlit
st.set_page_config(page_title="Control de Intercambiadores de Calor", layout="wide")

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
        font-size: 11px !important;
        padding: 6px 12px !important;
        font-weight: 700 !important;
        white-space: nowrap !important;
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
    }
    [data-testid="stTable"] td {
        font-size: 11px !important;
        padding: 5px 12px !important;
        white-space: nowrap !important;
        line-height: 1.2 !important;
        border: 1px solid #334155 !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CABECERA VISUAL
# -----------------------------------------------------------------------------
if os.path.exists("franja.jpg"):
    st.image("franja.jpg", use_container_width=True)

st.title("🔥 Consulta e Inspección de Intercambiadores de Calor")
st.markdown("---")

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE GOOGLE SHEETS Y DRIVE
# -----------------------------------------------------------------------------
SHEET_ID = "1lhpb211bqPyDAxxnBFgKaN7nY-WImR961xJ3mrIGYZ4"
NOMBRE_HOJA = "Hoja 1"

GDRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/10hv3MlaXaL4rZkQrssnROAX18ms_31rc"

MAPA_COLORES_ESTATUS = {
    "CHEQUEADO": "#28a745",        # Verde
    "NO CHEQUEADO": "#dc3545",     # Rojo
    "SIN INFORMACIÓN": "#6c757d"   # Gris
}

# -----------------------------------------------------------------------------
# CLASE Y FUNCIONES AUXILIARES PARA PDF Y TEXTO
# -----------------------------------------------------------------------------
class PDFCustom(FPDF):
    def footer(self):
        self.set_y(-18)
        logo_path = None
        for posible in ["logojn.png", "logojn.npg", "logo.png"]:
            if os.path.exists(posible):
                logo_path = posible
                break
        
        if logo_path:
            try:
                self.image(logo_path, x=170, y=self.get_y(), w=25)
            except Exception:
                pass

def normalizar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    nfkd_form = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower().strip()

def sanitizar_para_pdf(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return texto.encode('latin-1', 'replace').decode('latin-1')

def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def generar_link_gdrive(termino_busqueda):
    busqueda_encoded = urllib.parse.quote(str(termino_busqueda))
    return f"https://drive.google.com/drive/u/0/search?q={busqueda_encoded}"

def extraer_coordenadas(coordenadas):
    if pd.isna(coordenadas) or str(coordenadas).strip() in ['Sin información', 'nan', '']:
        return None, None
    numeros = re.findall(r'-?\d+[\.,]\d+', str(coordenadas))
    if len(numeros) >= 2:
        lat = numeros[0].replace(',', '.')
        lon = numeros[1].replace(',', '.')
        return lat, lon
    return None, None

def tiene_diseno_creado(val_equipo):
    """Verifica si el equipo tiene un archivo de configuración/diseño creado en el sistema."""
    val_clean = str(val_equipo).strip()
    posibles_archivos = [
        f"config_{val_clean}.json",
        f"config_{val_clean.upper()}.json",
        f"config_{val_clean.lower()}.json",
        f"config_{val_clean.replace('-', '')}.json",
        f"config_{val_clean.replace(' ', '')}.json"
    ]
    return any(os.path.exists(arch) for arch in posibles_archivos)

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

def calcular_total_conexiones_roscadas(df_sub, df_columns):
    col_roscadas = next((c for c in df_columns if 'ROSCAD' in str(c).upper() or 'PLUG' in str(c).upper()), None)
    col_eq = next((c for c in df_columns if 'EQUIPO' in str(c).upper()), None)
    total = 0
    
    for _, row in df_sub.iterrows():
        val_col = str(row[col_roscadas]).strip() if col_roscadas else ""
        if col_roscadas and val_col not in ['Sin información', 'SIN INFORMACIÓN', 'nan', '', 'None']:
            try:
                total += int(float(val_col))
                continue
            except ValueError:
                pass
        
        if col_eq:
            tag = str(row[col_eq]).strip()
            cfg = obtener_config_equipo(tag)
            if cfg:
                for noz in cfg.get("nozzles", []):
                    total += len(noz.get("auxiliaries", []))
                    if str(noz.get("style", "")).upper() in ["THREADED", "ROSCADA", "NPT", "TAPÓN / COUPLING"] or "THREAD" in str(noz.get("type", "")).upper():
                        total += 1
    return total

# -----------------------------------------------------------------------------
# MOTOR DE DIBUJO VECTORIAL DE RESERVA (FPDF)
# -----------------------------------------------------------------------------
def dibujar_esquema_fpdf(pdf, config, x_offset=15, y_offset=120):
    cy = y_offset + 25
    seq = config.get("components", {}).get("sequence", ["CHANNEL", "SHELL", "BONNET"])
    
    comp_lens = {
        "CHANNEL": float(config.get("components", {}).get("channel_length", 150)),
        "SHELL": float(config.get("components", {}).get("shell_length", 420)),
        "BONNET": float(config.get("components", {}).get("bonnet_length", 100))
    }
    
    total_len = sum(comp_lens.get(c, 100) for c in seq)
    scale = 130.0 / max(total_len, 1.0)
    
    r_shell = 15.0
    r_bonnet = 15.0
    
    coords = {}
    curr_x = x_offset + 25
    
    for comp in seq:
        w_scaled = comp_lens.get(comp, 100) * scale
        coords[comp] = {"start": curr_x, "end": curr_x + w_scaled, "width": w_scaled}
        curr_x += w_scaled + 2
        
    pdf.set_draw_color(239, 68, 68)
    pdf.line(x_offset + 10, cy, curr_x + 10, cy)
    
    shell_info = coords.get("SHELL", {"start": x_offset + 50, "width": 80})
    for sad in config.get("saddles", []):
        sad_ratio = float(sad.get("position_ratio", 0.5))
        sad_x = shell_info["start"] + shell_info["width"] * sad_ratio
        pdf.set_fill_color(100, 116, 139)
        pdf.set_draw_color(15, 23, 42)
        pdf.rect(sad_x - 4, cy + r_shell, 8, 7, 'FD')
        
    for idx, comp in enumerate(seq):
        c_info = coords[comp]
        cx = c_info["start"]
        cw = c_info["width"]
        
        if idx > 0:
            pdf.set_fill_color(71, 85, 105)
            pdf.set_draw_color(30, 41, 59)
            pdf.rect(cx - 2, cy - r_shell - 2, 2, r_shell * 2 + 4, 'FD')
            
        pdf.set_fill_color(226, 232, 240)
        pdf.set_draw_color(51, 65, 85)
        
        if comp == "BONNET":
            dome_w = min(r_bonnet * 0.6, cw * 0.45)
            if idx == len(seq) - 1 or idx > 0:
                pdf.ellipse(cx + cw - 2*dome_w, cy - r_bonnet, 2*dome_w, 2*r_bonnet, style='FD')
                pdf.rect(cx, cy - r_bonnet, cw - dome_w + 0.1, 2*r_bonnet, style='F')
                pdf.line(cx, cy - r_bonnet, cx + cw - dome_w, cy - r_bonnet)
                pdf.line(cx, cy + r_bonnet, cx + cw - dome_w, cy + r_bonnet)
                label_x = cx + (cw - dome_w) / 2 - 4
            else:
                pdf.ellipse(cx, cy - r_bonnet, 2*dome_w, 2*r_bonnet, style='FD')
                pdf.rect(cx + dome_w - 0.1, cy - r_bonnet, cw - dome_w + 0.1, 2*r_bonnet, style='F')
                pdf.line(cx + dome_w, cy - r_bonnet, cx + cw, cy - r_bonnet)
                pdf.line(cx + dome_w, cy + r_bonnet, cx + cw, cy + r_bonnet)
                label_x = cx + dome_w + (cw - dome_w) / 2 - 4

            pdf.set_font("Arial", "B", 7)
            pdf.set_text_color(51, 65, 85)
            pdf.text(label_x, cy + 1, "BONNET")
        else:
            pdf.rect(cx, cy - r_shell, cw, r_shell * 2, 'FD')
            pdf.set_font("Arial", "B", 7)
            pdf.set_text_color(51, 65, 85)
            pdf.text(cx + cw / 2 - 4, cy + 1, comp)

    for noz in config.get("nozzles", []):
        comp = noz.get("component", "SHELL")
        c_info = coords.get(comp, coords.get("SHELL"))
        ratio = float(noz.get("position_ratio", 0.5))
        nx = c_info["start"] + c_info["width"] * ratio
        
        style_type = noz.get("style", "FLANGED")
        side = noz.get("side", "TOP")
        tag_str = sanitizar_para_pdf(noz.get("tag", ""))
        
        auxs = noz.get("auxiliaries", [])
        aux_txt = sanitizar_para_pdf("/".join([a.get("position", "") for a in auxs if a.get("position")]))
        
        active_r = r_bonnet if comp == "BONNET" else r_shell
        
        if side == "TOP":
            ny = cy - active_r
            if style_type == "FLANGED":
                pdf.set_fill_color(203, 213, 225)
                pdf.set_draw_color(30, 41, 59)
                pdf.rect(nx - 2, ny - 9, 4, 9, 'FD')
                pdf.rect(nx - 4, ny - 11, 8, 2, 'FD')
                pdf.set_font("Arial", "B", 7)
                pdf.set_text_color(15, 23, 42)
                pdf.text(nx - 3, ny - 13, tag_str)
                if aux_txt:
                    pdf.set_font("Arial", "", 5)
                    pdf.text(nx - 3, ny - 4, aux_txt)
            else:
                pdf.set_fill_color(148, 163, 184)
                pdf.rect(nx - 1.5, ny - 5, 3, 5, 'FD')
                pdf.set_font("Arial", "B", 7)
                pdf.text(nx - 3, ny - 7, tag_str)
        else:
            ny = cy + active_r
            if style_type == "FLANGED":
                pdf.set_fill_color(203, 213, 225)
                pdf.set_draw_color(30, 41, 59)
                pdf.rect(nx - 2, ny, 4, 9, 'FD')
                pdf.rect(nx - 4, ny + 9, 8, 2, 'FD')
                pdf.set_font("Arial", "B", 7)
                pdf.set_text_color(15, 23, 42)
                pdf.text(nx - 3, ny + 15, tag_str)
                if aux_txt:
                    pdf.set_font("Arial", "", 5)
                    pdf.text(nx - 3, ny + 5, aux_txt)
            else:
                pdf.set_fill_color(148, 163, 184)
                pdf.rect(nx - 1.5, ny, 3, 5, 'FD')
                pdf.set_font("Arial", "B", 7)
                pdf.text(nx - 3, ny + 10, tag_str)
                
    pdf.set_y(y_offset + 60)

# -----------------------------------------------------------------------------
# DIBUJO DE LA TABLA NOZZLE SCHEDULE EN EL PDF
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL DE GENERACIÓN DEL PDF
# -----------------------------------------------------------------------------
def generar_pdf_equipo(val_equipo, val_unidad, valor_status, datos_mostrar, color_hex, titulo_doc, config_equipo=None):
    pdf = PDFCustom()
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()
    rgb = hex_to_rgb(color_hex)
    
    if not config_equipo:
        config_equipo = obtener_config_equipo(val_equipo)
    
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(*rgb)
    pdf.cell(0, 7, sanitizar_para_pdf(titulo_doc), ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    pdf.set_font("Arial", "B", 10)
    txt_equipo_unidad = f"EQUIPO: {sanitizar_para_pdf(val_equipo)}    |    UNIDAD DE PROCESO: {sanitizar_para_pdf(val_unidad)}"
    pdf.cell(0, 5, txt_equipo_unidad, ln=True, align="C")
    pdf.ln(2)
    
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*rgb)
    pdf.cell(0, 5, f"Estatus Actual: {sanitizar_para_pdf(valor_status)}", ln=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.ln(3)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, "Ficha Tecnica del Intercambiador", ln=True)
    pdf.ln(1)
    
    items_filtrados = [(str(k), str(v)) for k, v in datos_mostrar.items() if str(v).strip() != ""]
    ancho_columna = 93
    pdf.set_draw_color(*rgb)
    
    for i in range(0, len(items_filtrados), 2):
        k1, v1 = items_filtrados[i]
        k1_c = sanitizar_para_pdf(k1)
        v1_c = sanitizar_para_pdf(v1)
        
        if i + 1 < len(items_filtrados):
            k2, v2 = items_filtrados[i+1]
            k2_c = sanitizar_para_pdf(k2)
            v2_c = sanitizar_para_pdf(v2)
        else:
            k2_c, v2_c = "", ""
            
        lineas_v1 = max(1, int(len(v1_c) / 50) + 1)
        lineas_v2 = max(1, int(len(v2_c) / 50) + 1) if k2_c else 1
        max_lineas = max(lineas_v1, lineas_v2)
        
        altura_valor = max_lineas * 4.5 + 2
        
        if pdf.get_y() + altura_valor + 20 > 270:
            pdf.add_page()
            
        x_inicio = pdf.get_x()
        
        pdf.set_font("Arial", "B", 7.5)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(ancho_columna, 4.5, f"  {k1_c}", border="TRL", fill=True)
        pdf.cell(4, 4.5, "", border=0)
        
        if k2_c:
            pdf.cell(ancho_columna, 4.5, f"  {k2_c}", border="TRL", fill=True, ln=True)
        else:
            pdf.cell(ancho_columna, 4.5, "", border=0, ln=True)
            
        y_despues_titulos = pdf.get_y()
        
        pdf.set_xy(x_inicio, y_despues_titulos)
        pdf.set_font("Arial", "", 8)
        pdf.multi_cell(ancho_columna, 4.5, f"  {v1_c}", border="BRL")
        y_fin_izq = pdf.get_y()
        
        if k2_c:
            pdf.set_xy(x_inicio + ancho_columna + 4, y_despues_titulos)
            pdf.set_font("Arial", "", 8)
            pdf.multi_cell(ancho_columna, 4.5, f"  {v2_c}", border="BRL")
            y_fin_der = pdf.get_y()
            max_y = max(y_fin_izq, y_fin_der)
        else:
            max_y = y_fin_izq
            
        pdf.set_xy(x_inicio, max_y + 1)

    if config_equipo:
        if pdf.get_y() + 80 > 270:
            pdf.add_page()
            
        pdf.ln(3)
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(*rgb)
        pdf.cell(0, 6, "Plano Esquematico de Boquillas", ln=True)
        pdf.ln(4)
        
        y_esquema = pdf.get_y()
        dibujado_ok = False
        
        if generate_modular_exchanger_svg:
            try:
                import cairosvg
                svg_code = generate_modular_exchanger_svg(config_equipo)
                png_temp = f"temp_pdf_{sanitizar_para_pdf(val_equipo)}.png"
                cairosvg.svg2png(bytestring=svg_code.encode('utf-8'), write_to=png_temp, scale=2.5)
                pdf.image(png_temp, x=15, y=y_esquema, w=180)
                pdf.set_y(y_esquema + 88)
                if os.path.exists(png_temp):
                    os.remove(png_temp)
                dibujado_ok = True
            except Exception:
                dibujado_ok = False
                
        if not dibujado_ok:
            dibujar_esquema_fpdf(pdf, config_equipo, x_offset=15, y_offset=y_esquema + 5)
            
        agregar_tabla_nozzle_schedule_pdf(pdf, config_equipo, rgb)

    pdf.set_draw_color(0, 0, 0)
    
    try:
        out = pdf.output(dest='S')
        if isinstance(out, str):
            return out.encode('latin-1')
        elif isinstance(out, (bytes, bytearray)):
            return bytes(out)
    except Exception:
        pass
        
    out = pdf.output()
    if isinstance(out, str):
        return out.encode('latin-1')
    return bytes(out)

# -----------------------------------------------------------------------------
# CARGA AUTOMÁTICA DE DATOS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)
def cargar_datos(sheet_id, nombre_hoja):
    nombre_hoja_encoded = urllib.parse.quote(nombre_hoja)
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={nombre_hoja_encoded}"
    
    data = pd.read_csv(sheet_url)
    
    columnas = []
    conteo_columnas = {}
    for col in data.columns:
        col_clean = " ".join(str(col).split())
        if col_clean in conteo_columnas:
            conteo_columnas[col_clean] += 1
            columnas.append(f"{col_clean} ({conteo_columnas[col_clean]})")
        else:
            conteo_columnas[col_clean] = 1
            columnas.append(col_clean)
            
    data.columns = columnas
    data = data.fillna("Sin información")
    data = data.astype(str)
    
    for col in data.columns:
        if 'STATUS' in col.upper() or 'ESTATUS' in col.upper():
            data[col] = data[col].str.strip().str.upper()
            data[col] = data[col].replace({'NAN': 'SIN INFORMACIÓN', '': 'SIN INFORMACIÓN'})
            
    return data

try:
    df = cargar_datos(SHEET_ID, NOMBRE_HOJA)
except Exception as e:
    st.error(f"❌ Error al conectar con Google Sheets: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# RECONOCIMIENTO DE COLUMNAS CLAVE
# -----------------------------------------------------------------------------
col_unidad = next((c for c in df.columns if 'UNIDAD' in c.upper() or 'AREA' in c.upper() or 'ÁREA' in c.upper()), None)
col_equipo = next((c for c in df.columns if 'EQUIPO' in c.upper()), None)
col_status = next((c for c in df.columns if 'STATUS' in c.upper() or 'ESTATUS' in c.upper()), None)
col_comentario = next((c for c in df.columns if 'COMENTARIO' in c.upper()), None)
col_geo = next((c for c in df.columns if 'GEORREFERENCIA' in c.upper() or 'LAT' in c.upper() or 'COORD' in c.upper()), None)

# -----------------------------------------------------------------------------
# BARRA LATERAL: FILTROS
# -----------------------------------------------------------------------------
st.sidebar.header("🎯 Búsqueda e Inspección")
df_filtrado = df.copy()

if col_status:
    estados = ["Todos"] + sorted([x for x in df[col_status].unique() if x not in ["SIN INFORMACIÓN", "Sin información"]])
    status_sel = st.sidebar.selectbox("⚡ Filtrar por Estatus:", estados)
    if status_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_status] == status_sel]

if col_unidad:
    unidades = ["Todas"] + sorted([x for x in df_filtrado[col_unidad].unique() if x not in ["Sin información", "SIN INFORMACIÓN"]])
    unidad_sel = st.sidebar.selectbox("🏢 Unidad / Área de Proceso:", unidades)
    if unidad_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado[col_unidad] == unidad_sel]

if col_equipo:
    equipos = ["Todos"] + sorted([x for x in df_filtrado[col_equipo].unique() if x not in ["Sin información", "SIN INFORMACIÓN"]])
    equipo_sel = st.sidebar.selectbox("🔥 Seleccionar Equipo / Tag:", equipos)
    if equipo_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_equipo] == equipo_sel]

# -----------------------------------------------------------------------------
# RECUADRO DINÁMICO EN SIDEBAR: TOTAL CONEXIONES ROSCADAS (FILTRADO)
# -----------------------------------------------------------------------------
st.sidebar.markdown("---")
total_roscadas_filtrado = calcular_total_conexiones_roscadas(df_filtrado, df.columns)

st.sidebar.markdown(f"""
<div style="background: #1e293b; padding: 12px 14px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 15px; display: flex; align-items: center; gap: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
    <div style="flex-shrink: 0; background: #0f172a; padding: 8px; border-radius: 6px; display: flex; align-items: center; justify-content: center;">
        <svg width="32" height="32" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <polygon points="32,4 52,15 52,27 32,38 12,27 12,15" fill="#38bdf8" stroke="#0284c7" stroke-width="2"/>
            <polygon points="32,8 48,17 48,25 32,34 16,25 16,17" fill="#7dd3fc"/>
            <rect x="18" y="36" width="28" height="22" rx="2" fill="#bae6fd" stroke="#0284c7" stroke-width="2"/>
            <line x1="18" y1="41" x2="46" y2="41" stroke="#0284c7" stroke-width="2"/>
            <line x1="18" y1="46" x2="46" y2="46" stroke="#0284c7" stroke-width="2"/>
            <line x1="18" y1="51" x2="46" y2="51" stroke="#0284c7" stroke-width="2"/>
            <line x1="18" y1="56" x2="46" y2="56" stroke="#0284c7" stroke-width="2"/>
        </svg>
    </div>
    <div>
        <p style="margin: 0; font-size: 10px; color: #94a3b8; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">Total Conexiones Roscadas</p>
        <h3 style="margin: 2px 0 0 0; font-size: 22px; color: #38bdf8; font-weight: 700;">{total_roscadas_filtrado} <span style="font-size: 12px; font-weight: normal; color: #94a3b8;">Plugs/Cplgs</span></h3>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
for logo in ["logojn.png", "logojn.npg", "logo.png"]:
    if os.path.exists(logo):
        st.sidebar.image(logo, use_container_width=True)
        break

# -----------------------------------------------------------------------------
# VISTA PRINCIPAL
# -----------------------------------------------------------------------------
st.markdown(f"**Registros encontrados:** `{len(df_filtrado)}` de `{len(df)}` totales.")

pestana_tabla, pestana_stats = st.tabs(["📊 Vista General de Equipos", "📈 Panel General y Estadísticas"])

registro_seleccionado = None

with pestana_tabla:
    st.caption("💡 Haz clic en cualquier fila para abrir inmediatamente la Ficha Técnica del Intercambiador.")
    
    indices_ocultar = set(range(7, 29))
    cols_visibles = [
        col for idx, col in enumerate(df_filtrado.columns) 
        if idx not in indices_ocultar and 'CANTIDAD' not in col.upper()
    ]
    df_tabla_mostrar = df_filtrado[cols_visibles].copy()
    
    # Agregar columna visual indicando estado de plano / diseño (✅ Creado / ❌ Pendiente)
    if col_equipo and col_equipo in df_filtrado.columns:
        df_tabla_mostrar.insert(
            0, 
            "🖼️ Plano / Imagen", 
            df_filtrado[col_equipo].apply(lambda x: "✅ Creado" if tiene_diseno_creado(x) else "❌ Pendiente")
        )
    
    evento_tabla = st.dataframe(
        df_tabla_mostrar, 
        use_container_width=True, 
        selection_mode="single-row", 
        on_select="rerun"
    )

    if evento_tabla and "selection" in evento_tabla and "rows" in evento_tabla["selection"]:
        filas_seleccionadas = evento_tabla["selection"]["rows"]
        if len(filas_seleccionadas) > 0:
            indice_fila = filas_seleccionadas[0]
            registro_seleccionado = df_filtrado.iloc[indice_fila]

with pestana_stats:
    st.subheader("📊 Análisis Gráfico de Intercambiadores")
    
    if len(df_filtrado) == 0:
        st.warning("No hay datos disponibles para graficar con los filtros aplicados.")
    else:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("##### 📉 Estado de Inspección (STATUS)")
            if col_status:
                df_status_counts = df_filtrado[col_status].value_counts().reset_index()
                df_status_counts.columns = ['Estatus', 'Cantidad']
                fig_status = px.bar(
                    df_status_counts, 
                    x='Estatus', 
                    y='Cantidad', 
                    color='Estatus', 
                    color_discrete_map=MAPA_COLORES_ESTATUS, 
                    text='Cantidad'
                )
                fig_status.update_layout(showlegend=False, xaxis_title="", yaxis_title="Total Equipos")
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("No se encontró la columna de Status para graficar.")
                
        with col_g2:
            st.markdown("##### 🏢 Equipos por Unidad de Proceso")
            if col_unidad:
                df_unidad_counts = df_filtrado[col_unidad].value_counts().reset_index()
                df_unidad_counts.columns = ['Unidad', 'Cantidad']
                fig_unidad = px.bar(df_unidad_counts, x='Unidad', y='Cantidad', text='Cantidad')
                fig_unidad.update_layout(showlegend=False, xaxis_title="", yaxis_title="Total Equipos")
                st.plotly_chart(fig_unidad, use_container_width=True)
            else:
                st.info("No se encontró la columna de Unidad de Proceso para graficar.")

# -----------------------------------------------------------------------------
# DETALLE / FICHA TÉCNICA DEL INTERCAMBIADOR
# -----------------------------------------------------------------------------
if (registro_seleccionado is not None) or (len(df_filtrado) == 1):
    registro = registro_seleccionado if registro_seleccionado is not None else df_filtrado.iloc[0]
    
    st.markdown("---")
    
    col_detalles, col_enlaces = st.columns([2, 1])

    with col_detalles:
        val_equipo = registro[col_equipo] if col_equipo else "Detalle"
        val_unidad = registro[col_unidad] if col_unidad else "Sin unidad"
        val_equipo_clean = str(val_equipo).strip()
        
        st.subheader(f"📋 Ficha Técnica - Equipo {val_equipo}")
        
        datos_ficha_reducida = {}
        for k, v in registro.items():
            k_upper = str(k).upper()
            if 'UNIDAD' in k_upper and 'Unidad de Proceso' not in datos_ficha_reducida:
                datos_ficha_reducida['Unidad de Proceso'] = v
            elif 'EQUIPO' in k_upper and 'Equipo' not in datos_ficha_reducida:
                datos_ficha_reducida['Equipo'] = v
            elif 'COMENTARIO' in k_upper and 'Comentario' not in datos_ficha_reducida:
                datos_ficha_reducida['Comentario'] = v
        
        df_ficha = pd.DataFrame(list(datos_ficha_reducida.items()), columns=['Parámetro', 'Detalle'])
        st.table(df_ficha.style.hide(axis='index'))

        config_equipo = obtener_config_equipo(val_equipo_clean)

        st.markdown("### 📐 Plano Esquemático de Boquillas")
        if config_equipo and generate_modular_exchanger_svg:
            svg_code = generate_modular_exchanger_svg(config_equipo)
            
            html_encapsulado = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                * {{ box-sizing: border-box; }}
                html, body {{
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    height: 100%;
                    overflow: hidden;
                    background: transparent;
                }}
                .svg-container {{
                    width: 100%;
                    height: 100%;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    background: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                    padding: 4px;
                }}
                .svg-container svg {{
                    width: 100% !important;
                    height: 100% !important;
                    max-width: 100% !important;
                    max-height: 100% !important;
                    object-fit: contain;
                }}
            </style>
            </head>
            <body>
                <div class="svg-container">
                    {svg_code}
                </div>
            </body>
            </html>
            """
            
            components.html(html_encapsulado, height=470)
            
            st.markdown(f"#### 📋 NOZZLE SCHEDULE - {val_equipo_clean}")
            
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
                    "MK": noz.get("tag", ""),
                    "QT": 1,
                    "DESCRIPTION": desc_full,
                    "PROCESS": noz.get("service", "INLET"),
                    "AUXILLARIES": aux_combined
                })

            table_rows.append({
                "MK": "", "QT": "", "DESCRIPTION": "", "PROCESS": "", "AUXILLARIES": f"{global_aux_rating} CPLGS."
            })

            df_nozzles = pd.DataFrame(table_rows)
            st.table(df_nozzles.style.hide(axis='index'))

            col_plan1, col_plan2 = st.columns([3, 1])
            with col_plan1:
                st.success(f"✅ Plano esquemático y tabla de boquillas cargados para **{val_equipo_clean}**.")
            with col_plan2:
                if st.button("✏️ Editar Plano Esquemático"):
                    st.session_state["tag_para_diseño"] = val_equipo_clean
                    ir_base_diseno()
        else:
            st.info(f"ℹ️ El equipo **{val_equipo_clean}** aún no tiene un plano esquemático guardado.")
            if st.button(f"🛠️ Diseñar Plano Esquemático para {val_equipo_clean}", type="primary"):
                st.session_state["tag_para_diseño"] = val_equipo_clean
                ir_base_diseno()

    with col_enlaces:
        color_principal = "#005ce6"
        valor_status = "SIN INFORMACIÓN"
        if col_status and registro[col_status] not in ['Sin información', 'SIN INFORMACIÓN']:
            valor_status = registro[col_status].strip().upper()
            color_principal = MAPA_COLORES_ESTATUS.get(valor_status, "#005ce6")
            
        st.markdown(f"""
        <div style="background: transparent; padding: 12px; border-radius: 8px; text-align: center; border: 2px solid {color_principal}; margin-bottom: 12px;">
            <p style="margin: 0; font-size: 12px; color: #666; font-weight: bold; text-transform: uppercase;">Estatus del Equipo</p>
            <h3 style="margin: 4px 0 0 0; font-size: 22px; color: {color_principal}; line-height: 1.1;">{valor_status}</h3>
        </div>
        """, unsafe_allow_html=True)

        col_roscadas = next((c for c in df.columns if 'ROSCAD' in c.upper() or 'PLUG' in c.upper()), None)
        cant_roscadas = 0
        
        if col_roscadas and str(registro[col_roscadas]).strip() not in ['Sin información', 'SIN INFORMACIÓN', 'nan', '']:
            cant_roscadas = registro[col_roscadas]
        elif config_equipo:
            nozzles = config_equipo.get("nozzles", [])
            for noz in nozzles:
                cant_roscadas += len(noz.get("auxiliaries", []))
                if str(noz.get("style", "")).upper() in ["THREADED", "ROSCADA", "NPT", "TAPÓN / COUPLING"] or "THREAD" in str(noz.get("type", "")).upper():
                    cant_roscadas += 1

        st.markdown(f"""
        <div style="background: #ffffff; padding: 12px 16px; border-radius: 8px; border: 1px solid #cbd5e1; margin-bottom: 20px; display: flex; align-items: center; gap: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="flex-shrink: 0; background: #eff6ff; padding: 8px; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                <svg width="38" height="38" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <polygon points="32,4 52,15 52,27 32,38 12,27 12,15" fill="#2563eb" stroke="#1d4ed8" stroke-width="2"/>
                    <polygon points="32,8 48,17 48,25 32,34 16,25 16,17" fill="#60a5fa"/>
                    <rect x="18" y="36" width="28" height="22" rx="2" fill="#93c5fd" stroke="#1d4ed8" stroke-width="2"/>
                    <line x1="18" y1="41" x2="46" y2="41" stroke="#1d4ed8" stroke-width="2"/>
                    <line x1="18" y1="46" x2="46" y2="46" stroke="#1d4ed8" stroke-width="2"/>
                    <line x1="18" y1="51" x2="46" y2="51" stroke="#1d4ed8" stroke-width="2"/>
                    <line x1="18" y1="56" x2="46" y2="56" stroke="#1d4ed8" stroke-width="2"/>
                </svg>
            </div>
            <div>
                <p style="margin: 0; font-size: 11px; color: #64748b; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">Conexiones Roscadas (Este Equipo)</p>
                <h3 style="margin: 2px 0 0 0; font-size: 20px; color: #1e293b; font-weight: 700;">{cant_roscadas} <span style="font-size: 13px; font-weight: normal; color: #64748b;">(Plugs / Cplgs)</span></h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
            
        st.subheader("📁 Accesos Rápidos y Evidencia")
        
        termino_busqueda = val_equipo if val_equipo not in ["Sin información", "SIN INFORMACIÓN"] else val_unidad
            
        if termino_busqueda and termino_busqueda not in ["Sin información", "SIN INFORMACIÓN"]:
            url_gdrive = generar_link_gdrive(termino_busqueda)
            st.link_button(
                label=f"📂 Buscar Planos/Docs de '{termino_busqueda}' en Drive", 
                url=url_gdrive, 
                use_container_width=True
            )
            st.write("") 

        titulo_doc = f"Intercambiador {val_equipo} ({val_unidad})"
        pdf_bytes = generar_pdf_equipo(val_equipo, val_unidad, valor_status, datos_ficha_reducida, color_principal, titulo_doc, config_equipo=config_equipo)
        
        st.download_button(
            label="📄 Descargar Ficha PDF para Terreno",
            data=pdf_bytes,
            file_name=f"Ficha_Intercambiador_{val_equipo}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.write("")

        st.markdown("🖼️ **Evidencia / Fotografía de Inspección**")
        foto_subida = st.file_uploader("Sube o arrastra la imagen del equipo:", type=["png", "jpg", "jpeg"], key="visor_foto")
        
        if foto_subida is not None:
            st.image(foto_subida, caption=f"Evidencia - Equipo {val_equipo}", use_container_width=True)

        if col_geo and registro[col_geo] not in ['Sin información', 'SIN INFORMACIÓN']:
            lat, lon = extraer_coordenadas(registro[col_geo])
            if lat and lon:
                st.markdown("---")
                url_maps = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                st.link_button(
                    label="🗺️ Abrir Ubicación en Google Maps", 
                    url=url_maps, 
                    use_container_width=True
                )
                mapa_html = f"""
                <iframe 
                    width="100%" 
                    height="300" 
                    frameborder="0" 
                    scrolling="no" 
                    marginheight="0" 
                    marginwidth="0" 
                    src="https://maps.google.com/maps?q={lat},{lon}&hl=es&z=16&output=embed"
                    style="border-radius: 8px; border: 1px solid #ddd; margin-top: 10px;">
                </iframe>
                """
                st.markdown(mapa_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SECCIÓN INFERIOR: VISTA PREVIA 3D LIMPIA (SOLO LECTURA)
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("🔍 Vista Previa 3D de Equipos Registrados (Modo Presentación)")

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

db_equipos = cargar_db()

if not db_equipos:
    st.info("💡 Consejo: Guarda configuraciones desde la página de diseño para poder visualizarlas interactivamente aquí en 3D.")
else:
    tags_disponibles = list(db_equipos.keys())
    tag_visualizar = st.selectbox("Selecciona un equipo para inspeccionar en 3D:", tags_disponibles, key="preview_3d_select")

    if tag_visualizar and os.path.exists(HTML_FILE):
        datos_equipo = db_equipos[tag_visualizar]
        
        with open(HTML_FILE, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Ocultar automáticamente el panel lateral de edición (#ui-container) en el HTML inyectado
        html_limpio = html_content.replace(
            "body { margin: 0; background: #111; color: #fff; font-family: sans-serif; overflow: hidden; }",
            "body { margin: 0; background: #111; color: #fff; font-family: sans-serif; overflow: hidden; } #ui-container { display: none !important; }"
        )
        
        json_data_str = json.dumps(datos_equipo)
        html_injectado = html_limpio.replace(
            "/*__INJECT_DATA_HERE__*/", 
            f"window.initialExchangerData = {json_data_str};"
        )
        
        # Renderizar visor 3D limpio libre de controles de edición
        components.html(html_injectado, height=650, scrolling=False)
