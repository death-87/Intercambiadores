import os
import re
import unicodedata
import urllib.parse
import pandas as pd
import streamlit as st
import plotly.express as px
from fpdf import FPDF

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Gestión de Intercambiadores de Calor", layout="wide")

# Cabecera visual opcional
if os.path.exists("franja.jpg"):
    st.image("franja.jpg", use_container_width=True)

st.title("🔥 Sistema de Consulta e Inspección - Intercambiadores de Calor")
st.markdown("---")

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE ORIGEN DE DATOS
# -----------------------------------------------------------------------------
# Puedes usar una ruta local a tu archivo Excel o un enlace de Google Sheets
EXCEL_PATH_LOCAL = "intercambiadores.xlsx"  # Cambia por el nombre de tu archivo local

# Si prefieres usar Google Sheets, define estas variables:
USAR_GOOGLE_SHEETS = False
SHEET_ID = "TU_SHEET_ID_AQUI"
NOMBRE_HOJA = "Hoja1"

GDRIVE_FOLDER_URL = "https://drive.google.com"

# Paleta de colores para los estatus de mantenimiento/inspección
MAPA_COLORES_ESTATUS = {
    "OPERATIVO": "#28a745",               # Verde
    "EN MANTENIMIENTO": "#ff8c00",         # Naranjo
    "CRÍTICO / FALLA": "#dc3545",          # Rojo
    "PENDIENTE INSPECCIÓN": "#f1c40f",     # Amarillo
    "FUERA DE SERVICIO": "#6c757d"         # Gris
}

# -----------------------------------------------------------------------------
# CLASE Y FUNCIONES PARA GENERACIÓN DE PDF
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
    """Elimina tildes y pasa a minúsculas para comparaciones flexibles."""
    if not isinstance(texto, str):
        texto = str(texto)
    nfkd_form = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower().strip()

def sanitizar_para_pdf(texto):
    """Asegura compatibilidad con la codificación Latin-1 de FPDF."""
    if not isinstance(texto, str):
        texto = str(texto)
    return texto.encode('latin-1', 'replace').decode('latin-1')

def hex_to_rgb(hex_code):
    """Convierte colores hexadecimales a RGB para FPDF."""
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def generar_link_gdrive(termino_busqueda):
    """Genera enlace de búsqueda directa dentro de Google Drive."""
    busqueda_encoded = urllib.parse.quote(str(termino_busqueda))
    return f"https://drive.google.com/drive/u/0/search?q={busqueda_encoded}"

def extraer_coordenadas(coordenadas):
    """Extrae latitud y longitud si el Excel contiene coordenadas."""
    if pd.isna(coordenadas) or str(coordenadas).strip() in ['Sin información', 'nan', '']:
        return None, None
    numeros = re.findall(r'-?\d+[\.,]\d+', str(coordenadas))
    if len(numeros) >= 2:
        lat = numeros[0].replace(',', '.')
        lon = numeros[1].replace(',', '.')
        return lat, lon
    return None, None

def generar_pdf_ficha(tag_equipo, valor_status, datos_mostrar, color_hex, titulo_reporte):
    """Genera la ficha técnica del intercambiador de calor en PDF."""
    pdf = PDFCustom()
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()
    rgb = hex_to_rgb(color_hex)
    
    # 1. Título
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(*rgb)
    pdf.cell(0, 7, sanitizar_para_pdf(titulo_reporte), ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    # 2. TAG del Equipo
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 5, f"TAG EQUIPO: {sanitizar_para_pdf(tag_equipo)}", ln=True, align="C")
    pdf.ln(2)
    
    # 3. Estatus
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*rgb)
    pdf.cell(0, 5, f"Estatus Operativo: {sanitizar_para_pdf(valor_status)}", ln=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.ln(3)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, "Especificaciones Tecnicas e Inspeccion", ln=True)
    pdf.ln(1)
    
    # Filtrar columnas que no aportan valor visual
    items_filtrados = []
    palabras_excluidas = ["unnamed"]
    
    for k, v in datos_mostrar.items():
        k_str = str(k)
        if any(p in normalizar_texto(k_str) for p in palabras_excluidas):
            continue
        items_filtrados.append((k_str, str(v)))
    
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
        
        # Columna 1 Header
        pdf.set_font("Arial", "B", 7.5)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(ancho_columna, 4.5, f"  {k1_c}", border="TRL", fill=True)
        pdf.cell(4, 4.5, "", border=0)
        
        # Columna 2 Header
        if k2_c:
            pdf.cell(ancho_columna, 4.5, f"  {k2_c}", border="TRL", fill=True, ln=True)
        else:
            pdf.cell(ancho_columna, 4.5, "", border=0, ln=True)
            
        y_despues_titulos = pdf.get_y()
        
        # Columna 1 Valor
        pdf.set_xy(x_inicio, y_despues_titulos)
        pdf.set_font("Arial", "", 8)
        pdf.multi_cell(ancho_columna, 4.5, f"  {v1_c}", border="BRL")
        y_fin_izq = pdf.get_y()
        
        # Columna 2 Valor
        if k2_c:
            pdf.set_xy(x_inicio + ancho_columna + 4, y_despues_titulos)
            pdf.set_font("Arial", "", 8)
            pdf.multi_cell(ancho_columna, 4.5, f"  {v2_c}", border="BRL")
            y_fin_der = pdf.get_y()
            max_y = max(y_fin_izq, y_fin_der)
        else:
            max_y = y_fin_izq
            
        pdf.set_xy(x_inicio, max_y + 1)
        
    pdf.set_draw_color(0, 0, 0)
    return bytes(pdf.output())

# -----------------------------------------------------------------------------
# CARGA Y PROCESAMIENTO DE DATOS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def cargar_datos_excel(filepath_o_url, es_gsheets=False):
    if es_gsheets:
        nombre_hoja_encoded = urllib.parse.quote(NOMBRE_HOJA)
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_hoja_encoded}"
        data = pd.read_csv(url)
    else:
        # Carga desde un archivo local (.xlsx o .xls)
        data = pd.read_excel(filepath_o_url)
        
    data.columns = [" ".join(str(c).split()) for c in data.columns]
    data = data.loc[:, ~data.columns.duplicated()]
    data = data.fillna("Sin información")
    data = data.astype(str)
    
    return data

# Carga dinámicamente según archivo local o Google Sheets
try:
    if USAR_GOOGLE_SHEETS:
        df = cargar_datos_excel(SHEET_ID, es_gsheets=True)
    else:
        if os.path.exists(EXCEL_PATH_LOCAL):
            df = cargar_datos_excel(EXCEL_PATH_LOCAL)
        else:
            st.info("📌 Sube tu archivo Excel para comenzar el análisis:")
            uploaded_file = st.file_uploader("Cargar archivo Excel (.xlsx)", type=["xlsx", "xls"])
            if uploaded_file is not None:
                df = cargar_datos_excel(uploaded_file)
            else:
                st.stop()
except Exception as e:
    st.error(f"❌ Error al cargar los datos: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# DETECCIÓN AUTOMÁTICA DE COLUMNAS
# -----------------------------------------------------------------------------
col_tag = next((c for c in df.columns if any(k in c.upper() for k in ['TAG', 'EQUIPO', 'IDENTIFICADOR', 'CODIGO'])), df.columns[0])
col_area = next((c for c in df.columns if any(k in c.upper() for k in ['ÁREA', 'AREA', 'PLANTA', 'SECTOR'])), None)
col_tipo = next((c for c in df.columns if any(k in c.upper() for k in ['TIPO', 'MODELO', 'CLASE'])), None)
col_status = next((c for c in df.columns if any(k in c.upper() for k in ['ESTATUS', 'STATUS', 'ESTADO'])), None)
col_geo = next((c for c in df.columns if any(k in c.upper() for k in ['COORDENADAS', 'GEORREFERENCIA', 'LAT'])), None)

# -----------------------------------------------------------------------------
# PANEL LATERAL: FILTROS DINÁMICOS
# -----------------------------------------------------------------------------
st.sidebar.header("🎯 Filtros de Búsqueda")
df_filtrado = df.copy()

# 1. Filtro por TAG o Equipo
tags_disponibles = ["Todos"] + sorted([x for x in df[col_tag].unique() if x != "Sin información"])
tag_sel = st.sidebar.selectbox(f"🔍 Búsqueda por {col_tag}:", tags_disponibles)
if tag_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado[col_tag] == tag_sel]

# 2. Filtro por Estatus
if col_status:
    estatus_disponibles = ["Todos"] + sorted([x for x in df[col_status].unique() if x != "Sin información"])
    status_sel = st.sidebar.selectbox(f"⚡ Filtrar por {col_status}:", estatus_disponibles)
    if status_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_status] == status_sel]

st.sidebar.markdown("---")

# 3. Filtro por Planta / Área
if col_area:
    areas_disponibles = ["Todas"] + sorted([x for x in df[col_area].unique() if x != "Sin información"])
    area_sel = st.sidebar.selectbox(f"🏢 Filtrar por {col_area}:", areas_disponibles)
    if area_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado[col_area] == area_sel]

# 4. Filtro por Tipo de Intercambiador
if col_tipo:
    tipos_disponibles = ["Todos"] + sorted([x for x in df[col_tipo].unique() if x != "Sin información"])
    tipo_sel = st.sidebar.selectbox(f"🛠️ Filtrar por {col_tipo}:", tipos_disponibles)
    if tipo_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_tipo] == tipo_sel]

st.sidebar.markdown("---")
for logo in ["logojn.png", "logojn.npg", "logo.png"]:
    if os.path.exists(logo):
        st.sidebar.image(logo, use_container_width=True)
        break

# -----------------------------------------------------------------------------
# VISTA PRINCIPAL: TABLA Y ESTADÍSTICAS
# -----------------------------------------------------------------------------
st.markdown(f"**Equipos encontrados:** `{len(df_filtrado)}` de `{len(df)}` registrados.")

pestana_tabla, pestana_stats = st.tabs(["📊 Vista General de Equipos", "📈 Panel Gráfico y Análisis"])

registro_seleccionado = None

with pestana_tabla:
    st.caption("💡 Haz clic en cualquier fila para desplegar la Ficha Técnica del intercambiador de calor.")
    
    evento_tabla = st.dataframe(
        df_filtrado, 
        use_container_width=True, 
        selection_mode="single-row", 
        on_select="rerun"
    )

    if evento_tabla and "selection" in evento_tabla and "rows" in evento_tabla["selection"]:
        filas = evento_tabla["selection"]["rows"]
        if len(filas) > 0:
            registro_seleccionado = df_filtrado.iloc[filas[0]]

with pestana_stats:
    st.subheader("📊 Métricas Generales")
    if len(df_filtrado) == 0:
        st.warning("No hay datos disponibles para las estadísticas con los filtros seleccionados.")
    else:
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("##### 📉 Distribución por Estatus Operativo")
            if col_status:
                df_st = df_filtrado[col_status].value_counts().reset_index()
                df_st.columns = ['Estatus', 'Cantidad']
                fig_st = px.bar(df_st, x='Estatus', y='Cantidad', color='Estatus', color_discrete_map=MAPA_COLORES_ESTATUS, text='Cantidad')
                fig_st.update_layout(showlegend=False, xaxis_title="", yaxis_title="Total Equipos")
                st.plotly_chart(fig_st, use_container_width=True)
            else:
                st.info("No se identificó una columna de Estatus.")

        with col_g2:
            st.markdown("##### ⚙️ Equipos por Planta / Área")
            if col_area:
                df_ar = df_filtrado[col_area].value_counts().reset_index()
                df_ar.columns = ['Área', 'Cantidad']
                fig_ar = px.bar(df_ar, x='Área', y='Cantidad', text='Cantidad')
                fig_ar.update_layout(showlegend=False, xaxis_title="", yaxis_title="Total Equipos")
                st.plotly_chart(fig_ar, use_container_width=True)
            else:
                st.info("No se identificó una columna de Área o Planta.")

# -----------------------------------------------------------------------------
# FICHA TÉCNICA Y ACCIONES PARA EL EQUIPO SELECCIONADO
# -----------------------------------------------------------------------------
if (registro_seleccionado is not None) or (len(df_filtrado) == 1):
    registro = registro_seleccionado if registro_seleccionado is not None else df_filtrado.iloc[0]
    
    st.markdown("---")
    val_tag = registro[col_tag] if col_tag else "Equipo"
    
    col_detalles, col_enlaces = st.columns([2, 1])

    with col_detalles:
        st.subheader(f"📋 Ficha Técnica - TAG: {val_tag}")
        datos_mostrar = {k: v for k, v in registro.items() if "Unnamed" not in str(k)}
        df_ficha = pd.DataFrame(list(datos_mostrar.items()), columns=['Parámetro / Campo', 'Valor'])
        st.table(df_ficha)

    with col_enlaces:
        color_principal = "#005ce6"
        valor_status = "SIN INFORMACIÓN"
        
        if col_status and registro[col_status] != 'Sin información':
            valor_status = registro[col_status].strip().upper()
            color_principal = MAPA_COLORES_ESTATUS.get(valor_status, "#005ce6")
            
        st.markdown(f"""
        <div style="background: transparent; padding: 12px; border-radius: 8px; text-align: center; border: 2px solid {color_principal}; margin-bottom: 20px;">
            <p style="margin: 0; font-size: 12px; color: #666; font-weight: bold; text-transform: uppercase;">Estado del Intercambiador</p>
            <h3 style="margin: 4px 0 0 0; font-size: 20px; color: {color_principal}; line-height: 1.1;">{valor_status}</h3>
        </div>
        """, unsafe_allow_html=True)
            
        st.subheader("📁 Evidencia y Documentación")
        
        # Enlace a Google Drive
        url_gdrive = generar_link_gdrive(val_tag)
        st.link_button(
            label=f"📂 Buscar Planos / OT de '{val_tag}'", 
            url=url_gdrive, 
            use_container_width=True
        )
        st.write("") 

        # Generación de PDF
        pdf_bytes = generar_pdf_ficha(val_tag, valor_status, datos_mostrar, color_principal, f"Ficha Técnica - Intercambiador {val_tag}")
        st.download_button(
            label="📄 Descargar Ficha PDF para Terreno",
            data=pdf_bytes,
            file_name=f"Ficha_Intercambiador_{val_tag}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.write("")

        # Carga de fotos / inspección en terreno
        st.markdown("🖼️ **Registro Fotográfico / Inspección**")
        foto_subida = st.file_uploader("Subir imagen o evidencia del equipo:", type=["png", "jpg", "jpeg"], key="visor_foto")
        
        if foto_subida is not None:
            st.image(foto_subida, caption=f"Evidencia - TAG {val_tag}", use_container_width=True)

        # Mapa de ubicación si existe columna de coordenadas
        if col_geo and registro[col_geo] != 'Sin información':
            lat, lon = extraer_coordenadas(registro[col_geo])
            if lat and lon:
                st.markdown("---")
                url_maps = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                st.link_button(
                    label="🗺️ Ver Ubicación en Google Maps", 
                    url=url_maps, 
                    use_container_width=True
                )
```

---

### 🔥 ¿Qué debes ajustar cuando tengas tu Excel listo?

1. **Ruta del Excel:** Cambia `"intercambiadores.xlsx"` por el nombre exacto de tu archivo dentro de la misma carpeta.
2. **Detección Automática de Columnas:** El script busca automáticamente términos clave en tus encabezados:
   - **TAG / Identificador:** Busca columnas con "TAG", "EQUIPO", "CODIGO".
   - **Estatus:** Busca "ESTATUS", "STATUS" o "ESTADO".
   - **Área:** Busca "ÁREA", "PLANTA", "SECTOR".
   - **Tipo:** Busca "TIPO", "MODELO", "CLASE".
3. **Librerías Requeridas:** Para ejecutar esta versión con archivos Excel locales, asegúrate de instalar `openpyxl`:
   ```bash
   pip install streamlit pandas plotly fpdf openpyxl