import os
import re
import unicodedata
import urllib.parse
import pandas as pd
import streamlit as st
import plotly.express as px
from fpdf import FPDF

# Configuración de página de Streamlit
st.set_page_config(page_title="Control de Intercambiadores de Calor", layout="wide")

# -----------------------------------------------------------------------------
# CABECERA VISUAL
# -----------------------------------------------------------------------------
if os.path.exists("franja.jpg"):
    st.image("franja.jpg", use_container_width=True)

st.title("🔥 Consulta e Inspección de Intercambiadores de Calor")
st.markdown("---")

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE GOOGLE SHEETS
# -----------------------------------------------------------------------------
SHEET_ID = "1lhpb211bqPyDAxxnBFgKaN7nY-WImR961xJ3mrIGYZ4"
NOMBRE_HOJA = "Hoja 1"

GDRIVE_FOLDER_URL = "[https://drive.google.com/drive/folders/1zGSlDQu5o9waFqm211P344MAqxCC8AAK](https://drive.google.com/drive/folders/1zGSlDQu5o9waFqm211P344MAqxCC8AAK)"

# Paleta de colores para estatus de inspección / mantenimiento
MAPA_COLORES_ESTATUS = {
    "CHEQUEADO": "#28a745",          # Verde
    "PENDIENTE": "#dc3545",          # Rojo
    "EN REVISIÓN": "#d35400",        # Naranjo oscuro
    "REPARADO": "#ff8c00",           # Naranjo
    "SIN INFORMACIÓN": "#6c757d"     # Gris
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
    """Elimina tildes y pasa a minúsculas para comparaciones exactas."""
    if not isinstance(texto, str):
        texto = str(texto)
    nfkd_form = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower().strip()

def sanitizar_para_pdf(texto):
    """Asegura compatibilidad con codificación Latin-1 de FPDF."""
    if not isinstance(texto, str):
        texto = str(texto)
    return texto.encode('latin-1', 'replace').decode('latin-1')

def hex_to_rgb(hex_code):
    """Convierte un color HEX a una tupla RGB para FPDF."""
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def generar_link_gdrive(termino_busqueda):
    """Genera un enlace de búsqueda directa dentro de Google Drive."""
    busqueda_encoded = urllib.parse.quote(str(termino_busqueda))
    return f"[https://drive.google.com/drive/u/0/search?q=](https://drive.google.com/drive/u/0/search?q=){busqueda_encoded}"

def extraer_coordenadas(coordenadas):
    """Extrae latitud y longitud desde un string de coordenadas si existe."""
    if pd.isna(coordenadas) or str(coordenadas).strip() in ['Sin información', 'nan', '']:
        return None, None
    numeros = re.findall(r'-?\d+[\.,]\d+', str(coordenadas))
    if len(numeros) >= 2:
        lat = numeros[0].replace(',', '.')
        lon = numeros[1].replace(',', '.')
        return lat, lon
    return None, None

def generar_pdf_equipo(val_equipo, val_unidad, valor_status, datos_mostrar, color_hex, titulo_doc):
    """Genera el reporte PDF para terreno."""
    pdf = PDFCustom()
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()
    rgb = hex_to_rgb(color_hex)
    
    # 1. Título Principal
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(*rgb)
    pdf.cell(0, 7, sanitizar_para_pdf(titulo_doc), ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    # 2. Equipo y Unidad
    pdf.set_font("Arial", "B", 10)
    txt_equipo_unidad = f"EQUIPO: {sanitizar_para_pdf(val_equipo)}   |   UNIDAD DE PROCESO: {sanitizar_para_pdf(val_unidad)}"
    pdf.cell(0, 5, txt_equipo_unidad, ln=True, align="C")
    pdf.ln(2)
    
    # 3. Estatus Actual
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*rgb)
    pdf.cell(0, 5, f"Estatus Actual: {sanitizar_para_pdf(valor_status)}", ln=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.ln(3)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, "Detalle Tecnico y Conexiones del Intercambiador", ln=True)
    pdf.ln(1)
    
    # Filtrado de campos no deseados
    items_filtrados = []
    palabras_excluidas = ["unnamed", "status", "estatus", "foto de referencia"]
    
    for k, v in datos_mostrar.items():
        k_str = str(k)
        if any(p in normalizar_texto(k_str) for p in palabras_excluidas):
            continue
        if str(v).strip() != "" and str(v).strip().lower() != "sin información":
            items_filtrados.append((k_str, str(v)))
    
    ancho_columna = 93
    pdf.set_draw_color(*rgb)
    
    for i in range(0, len(items_filtrados), 2):
        k1, v1 = items_filtrados[i]
        k1_c = sanitizar_para_pdf(k1)
        v1_c = sanitizar_para_pdf(v
